<?php

declare(strict_types=1);

namespace App\Controller\Admin;

use App\Model\Database\Entities\AssignmentProfile;
use App\Model\Database\Types\LogType;
use App\Model\Database\Types\ProfileType;

/**
 * Controller sloužící k nastavování profilů zadání.
 *
 * @author Michal Turek
 */
class ProfilesController extends BaseAdminController
{
    protected function process(): void
    {
        if (!$this->loggedUser->isAdmin) {
            $this->error404();
            return;
        }

        $action = $_GET['action'] ?? 'default';
        switch ($action) {
            case 'default':
                $this->actionDefault();
                break;
            case 'add':
                $this->actionAdd();
                break;
            case 'edit':
                $this->actionEdit();
                break;
            case 'delete':
                $this->actionDelete();
                break;
            default:
                $this->error404();
                return;
        }
        $this->templateData['action'] = $action;
    }

    // AKCE

    /**
     * Výchozí akce, vypíše seznam profilů.
     */
    private function actionDefault(): void
    {
        $this->templateData['profiles'] = $this->getDatabase()->getAllAssignmentProfiles();
    }

    /**
     * Akce pro přidání nových profilů zadání.
     */
    private function actionAdd(): void
    {
        if (isset($_POST['admin_profiles_add_form'])) {
            $this->processProfilesAddForm();
        }
    }

    /**
     * Akce pro úpravu profilů zadání.
     */
    private function actionEdit(): void
    {
        if (!isset($_GET['id'])) {
            $this->error404();
            return;
        }

        $id = (int) $_GET['id'];
        $profile = $this->getDatabase()->getAssignmentProfileById($id);
        if (!$profile) {
            $this->error404();
            return;
        }

        if (isset($_POST['admin_profiles_edit_form'])) {
            $this->processProfileEditForm($profile);
        } else {
            $this->templateData['post'] = [
                'name' => $profile->name,
                'type' => $profile->type->value,
                'options' => $profile->options,
            ];
            switch ($profile->type) {
                case ProfileType::DOCUMENT:
                    $this->templateData['post']['doc'] = $profile->options;
                    break;
                case ProfileType::TABLE_PROCESSOR:
                    $this->templateData['post']['table'] = $profile->options;
                    break;
            }
        }
    }

    /**
     * Akce pro smazání konkrétního profilu zadání. Po smazání je uživatel přesměrován zpět na seznam profilů.
     */
    private function actionDelete(): void
    {
        if (!isset($_GET['id'])) {
            $this->error404();
            return;
        }

        $id = (int) $_GET['id'];
        $profile = $this->getDatabase()->getAssignmentProfileById($id);
        if (!$profile) {
            $this->error404();
            return;
        }

        if (!$this->getDatabase()->removeAssignmentProfile($id)) {
            $this->alertMessage('danger', 'Nepodařilo se odebrat profil zadání. Zřejmě je používán');
            $this->redirect('admin/profiles');
        }
        $this->getDatabase()->log('Uživatel odebral profil zadání s ID ' . $id, LogType::PROFILE_DELETE, userId: $this->loggedUser->id);
        $this->alertMessage('success', 'Profil byl úspěšně odebrán');
        $this->redirect('admin/profiles');
    }

    // FORMULÁŘE

    /**
     * Metoda pro zpracování vytvoření nového profilu zadání.
     */
    private function processProfilesAddForm(): void
    {
        $post = [];

        $missing = false;

        if (isset($_POST['name'])) {
            $post['name'] = $_POST['name'];
        } else {
            $missing = true;
        }

        if (isset($_POST['type'])) {
            $post['type'] = $_POST['type'];
        } else {
            $missing = true;
        }

        if (isset($_POST['doc']) && is_array($_POST['doc'])) {
            $post['doc'] = $_POST['doc'];
        }

        if (isset($_POST['table']) && is_array($_POST['table'])) {
            $post['table'] = $_POST['table'];
        }

        $this->templateData['post'] = $post;

        if ($missing) {
            $this->alertMessage('danger', 'Nejsou vyplněna všechna požadovaná pole');
            return;
        }

        $profileType = ProfileType::tryFrom($post['type']);
        if ($profileType === null) {
            $this->alertMessage('danger', 'Typ profilu nebyl vybrán');
            return;
        }

        $options = match ($profileType) {
            ProfileType::DOCUMENT => $post['doc'],
            ProfileType::TABLE_PROCESSOR => $post['table'],
        } ?? [];

        $profileId = $this->getDatabase()->createAssignmentProfile($post['name'], $profileType, $options);
        if ($profileId === false) {
            $this->alertMessage('danger', 'Nepodařilo se vytvořit nový profil zadání');
            return;
        }

        if ($profileType === ProfileType::DOCUMENT) {
            // pokud se jedná o zadání typu dokument, zpracujeme uložení nahraných souborů s texty pro generátor
            $this->processDocumentUpload($profileId);
        }

        $this->getDatabase()->log('Vytvořil nový profil zadání ' . $post['name'] . ' (Typ ' . $profileType->name . '; ID ' . $profileId . ')', LogType::PROFILE_ADD, userId: $this->loggedUser->id);
        $this->alertMessage('success', 'Profil zadání byl úspěšně vytvořen');
        $this->redirect('admin/profiles');
    }

    /**
     * Metoda pro zpracování formuláře na úpravu existujícího profilu zadání.
     *
     * @param AssignmentProfile $profile profil zadání, který má být upravován
     */
    private function processProfileEditForm(AssignmentProfile $profile): void
    {
        $post = [];

        $missing = false;

        if (isset($_POST['name'])) {
            $post['name'] = $_POST['name'];
        } else {
            $missing = true;
        }

        if (isset($_POST['type'])) {
            $post['type'] = $_POST['type'];
        } else {
            $missing = true;
        }

        if (isset($_POST['doc']) && is_array($_POST['doc'])) {
            $post['doc'] = $_POST['doc'];
        }

        if (isset($_POST['table']) && is_array($_POST['table'])) {
            $post['table'] = $_POST['table'];
        }

        $this->templateData['post'] = $post;

        if ($missing) {
            $this->alertMessage('danger', 'Nejsou vyplněna všechna požadovaná pole');
            return;
        }

        $profileType = ProfileType::tryFrom($post['type']);
        if ($profileType === null) {
            $this->alertMessage('danger', 'Typ profilu nebyl vybrán');
            return;
        }

        $options = match ($profileType) {
            ProfileType::DOCUMENT => $post['doc'],
            ProfileType::TABLE_PROCESSOR => $post['table'],
        } ?? [];

        $result = $this->getDatabase()->updateAssignmentProfile($profile->id, $post['name'], $profileType, $options);
        if ($result === false) {
            $this->alertMessage('danger', 'Nepodařilo se upravit profil zadání');
            return;
        }

        if ($profileType === ProfileType::DOCUMENT) {
            // pokud se jedná o zadání typu dokument, zpracujeme uložení nahraných souborů s texty pro generátor
            $this->processDocumentUpload($profile->id);
        }

        $this->getDatabase()->log('Upraven profil zadání ' . $post['name'] . ' (' . $profileType->name . '; ID ' . $profile->id . ')', LogType::PROFILE_EDIT, userId: $this->loggedUser->id);
        $this->alertMessage('success', 'Profil zadání byl úspěšně upraven');
        $this->redirect('admin/profiles');
    }

    /**
     * Metoda zpracuje uložení souborů z formuláře pro profil zadání typu dokument.
     *
     * @param int $profileId ID profilu zadání
     */
    private function processDocumentUpload(int $profileId): void
    {
        if (isset($_FILES['doc_file']['tmp_name']['sentences'], $_FILES['doc_file']['error']['sentences']) && $_FILES['doc_file']['error']['sentences'] === 0) {
            @mkdir(DOCUMENT_FOLDER . '/texts/' . $profileId, recursive: true);
            move_uploaded_file($_FILES['doc_file']['tmp_name']['sentences'], DOCUMENT_FOLDER . '/texts/' . $profileId . '/sentences.txt');
        }
        if (isset($_FILES['doc_file']['tmp_name']['title'], $_FILES['doc_file']['error']['title'])  && $_FILES['doc_file']['error']['title'] === 0) {
            @mkdir(DOCUMENT_FOLDER . '/texts/' . $profileId, recursive: true);
            move_uploaded_file($_FILES['doc_file']['tmp_name']['title'], DOCUMENT_FOLDER . '/texts/' . $profileId . '/title.txt');
        }
        if (isset($_FILES['doc_file']['tmp_name']['captions'], $_FILES['doc_file']['error']['captions']) && $_FILES['doc_file']['error']['captions'] === 0) {
            @mkdir(DOCUMENT_FOLDER . '/texts/' . $profileId, recursive: true);
            move_uploaded_file($_FILES['doc_file']['tmp_name']['captions'], DOCUMENT_FOLDER . '/texts/' . $profileId . '/caption.txt');
        }
        if (isset($_FILES['doc_file']['tmp_name']['topics'], $_FILES['doc_file']['error']['topics']) && $_FILES['doc_file']['error']['topics'] === 0) {
            @mkdir(DOCUMENT_FOLDER . '/texts/' . $profileId, recursive: true);
            move_uploaded_file($_FILES['doc_file']['tmp_name']['topics'], DOCUMENT_FOLDER . '/texts/' . $profileId . '/topic.txt');
        }
        if (isset($_FILES['doc_file']['tmp_name']['list'], $_FILES['doc_file']['error']['list']) && $_FILES['doc_file']['error']['list'] === 0) {
            @mkdir(DOCUMENT_FOLDER . '/texts/' . $profileId, recursive: true);
            move_uploaded_file($_FILES['doc_file']['tmp_name']['list'], DOCUMENT_FOLDER . '/texts/' . $profileId . '/list.json');
        }
        if (isset($_FILES['doc_file']['tmp_name']['bibliography'], $_FILES['doc_file']['error']['bibliography']) && $_FILES['doc_file']['error']['bibliography'] === 0) {
            @mkdir(DOCUMENT_FOLDER . '/texts/' . $profileId, recursive: true);
            move_uploaded_file($_FILES['doc_file']['tmp_name']['bibliography'], DOCUMENT_FOLDER . '/texts/' . $profileId . '/bibliography.json');
        }
    }
}
