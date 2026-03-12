<?php

declare(strict_types=1);

namespace App\Controller\Admin;

use App\Model\Database\Entities\User;
use App\Model\Database\Types\LogType;

/**
 * Controller sloužící pro zprávu uživatelů v systému.
 *
 * @author Michal Turek
 */
class UsersController extends BaseAdminController
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
     * Výchozí akce, slouží k výpisu administrátorů a vyučujících v systému.
     */
    private function actionDefault(): void
    {
        $this->templateData['admins'] = $this->getDatabase()->getAllAdminUsers();
    }

    /**
     * Akce pro přidání nového vyučujícího nebo administrátora
     */
    private function actionAdd(): void
    {
        if (isset($_POST['admin_users_add_form'])) {
            $this->processUserAddForm();
        }
    }

    /**
     * Akce pro úpravu vyučujícího nebo administrátora
     */
    private function actionEdit(): void
    {
        if (!isset($_GET['id'])) {
            $this->error404();
            return;
        }

        $id = (int) $_GET['id'];
        $user = $this->getDatabase()->getAdminUserById($id);
        if (!$user) {
            $this->error404();
            return;
        }

        // Uživatele s ID 1 není možné v aplikaci upravovat.
        if ($user->id === 1) {
            $this->alertMessage('danger', 'Tohoto uživatele není možné upravovat!');
            $this->redirect('admin/users');
            return;
        }

        if (isset($_POST['admin_users_edit_form'])) {
            $this->processUserEditForm($user);
        } else {
            $this->templateData['post'] = [
                'username' => $user->username,
                'name' => $user->name,
                'surname' => $user->surname,
                'role' => $user->isAdmin ? '1' : '0',
            ];
        }
        $this->templateData['editedUserId'] = $id;
    }

    /**
     * Akce pro odstranění uživatele v systému
     */
    private function actionDelete(): void
    {
        if (!isset($_GET['id'])) {
            $this->error404();
            return;
        }

        $id = (int) $_GET['id'];
        $user = $this->getDatabase()->getAdminUserById($id);
        if (!$user) {
            $this->error404();
            return;
        }

        // Uživatele s ID 1 není možné odstranit.
        if ($user->id === 1) {
            $this->alertMessage('danger', 'Tohoto uživatele není možné odstranit!');
            $this->redirect('admin/users');
            return;
        }

        $result = $this->getDatabase()->removeAdminUser($id);
        if (!$result) {
            $this->alertMessage('danger', 'Uživatele se nepodařilo odebrat');
            $this->redirect('admin/users');
        }

        $this->getDatabase()->log('Uživatel odebral uživatele s ID ' . $id, LogType::USER_DELETE, userId: $this->loggedUser->id);
        $this->alertMessage('success', 'Uživatel byl úspěšně odebrán');
        $this->redirect('admin/users');
    }

    // FORMULÁŘE

    /**
     * Metoda pro zpracování formuláře na vytvoření nového administrátora/vyučujícího.
     */
    private function processUserAddForm(): void
    {
        $post = [];

        $missing = false;

        if (isset($_POST['name'])) {
            $post['name'] = $_POST['name'];
        } else {
            $missing = true;
        }

        if (isset($_POST['surname'])) {
            $post['surname'] = $_POST['surname'];
        } else {
            $missing = true;
        }

        if (isset($_POST['username'])) {
            $post['username'] = $_POST['username'];
        } else {
            $missing = true;
        }

        if (isset($_POST['password'])) {
            $post['password'] = $_POST['password'];
        } else {
            $missing = true;
        }

        if (isset($_POST['passwordAgain'])) {
            $post['passwordAgain'] = $_POST['passwordAgain'];
        } else {
            $missing = true;
        }

        if (isset($_POST['role'])) {
            $post['role'] = $_POST['role'];
        } else {
            $missing = true;
        }

        $this->templateData['post'] = $post;

        if ($missing) {
            $this->alertMessage('danger', 'Nejsou vyplněna všechna požadovaná pole');
            return;
        }

        if ($post['password'] !== $post['passwordAgain']) {
            $this->alertMessage('danger', 'Hesla se neshodují');
            return;
        }

        if ($this->getDatabase()->checkIfAdminUsernameExists($post['username'])) {
            $this->alertMessage('danger', 'Toto uživatelské jméno se již používá');
            return;
        }

        $userId = $this->getDatabase()->createAdminUser($post['username'], $post['name'], $post['surname'], $post['password'], $post['role'] === '1');
        if ($userId === false) {
            $this->alertMessage('danger', 'Nepodařilo se vytvořit uživatele');
            return;
        }

        $this->getDatabase()->log('Vytvořil nového uživatele ' . $post['username'] . ' (' . $post['name'] . ' ' . $post['surname'] . '; ID ' . $userId . '; role ' . ($post['role'] === '1' ? 'Administrátor' : 'Vyučující') . ')' .')', LogType::USER_ADD, userId: $this->loggedUser->id);
        $this->alertMessage('success', 'Uživatel byl úspěšně vytvořen');
        $this->redirect('admin/users');
    }

    /**
     * Metoda pro zpracování formuláře na editaci administrátora nebo vyučujícího.
     *
     * @param User $user upravovaný uživatel
     */
    private function processUserEditForm(User $user): void
    {
        $post = [];

        $missing = false;

        if (isset($_POST['name'])) {
            $post['name'] = $_POST['name'];
        } else {
            $missing = true;
        }

        if (isset($_POST['surname'])) {
            $post['surname'] = $_POST['surname'];
        } else {
            $missing = true;
        }

        if (isset($_POST['username'])) {
            $post['username'] = $_POST['username'];
        } else {
            $missing = true;
        }

        // Administrátor nemůže ponížit vlastní roli
        if ($this->loggedUser->id === $user->id) {
            $post['role'] = '1';
        } else if (isset($_POST['role'])) {
            $post['role'] = $_POST['role'];
        } else {
            $missing = true;
        }

        $this->templateData['post'] = $post;

        if ($missing) {
            $this->alertMessage('danger', 'Nejsou vyplněna všechna požadovaná pole');
            return;
        }

        if ($user->username !== $post['username'] && $this->getDatabase()->checkIfAdminUsernameExists($post['username'])) {
            $this->alertMessage('danger', 'Toto uživatelské jméno se již používá');
            return;
        }

        $result = $this->getDatabase()->updateAdminUser($user->id, $post['username'], $post['name'], $post['surname'], $post['role'] === '1');
        if ($result === false) {
            $this->alertMessage('danger', 'Nepodařilo se upravit uživatele');
            return;
        }

        $this->getDatabase()->log('Upraven uživatel ' . $post['username'] . ' (' . $post['name'] . ' ' . $post['surname'] . '; ID ' . $user->id . '; role ' . ($post['role'] === '1' ? 'Administrátor' : 'Vyučující') . ')' .')', LogType::USER_EDIT, userId: $this->loggedUser->id);
        $this->alertMessage('success', 'Uživatel byl úspěšně upraven');
        $this->redirect('admin/users');
    }
}
