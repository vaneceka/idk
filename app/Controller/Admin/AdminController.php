<?php

declare(strict_types=1);

namespace App\Controller\Admin;

use App\Model\Database\Types\LogType;
use App\Model\Database\Types\Options;
use App\Model\Database\Types\Semester;
use App\Model\Session;

/**
 * Controller představující hlavní stránku administrace.
 * Pro nepřihlášeného uživatele je zobrazena přihlašovací stránka.
 * Pro přihlášeného uživatele je zobrazen seznam předmětů, ke kterým má přístup, případně seznam rozvrhových akcí v předmětu.
 *
 * @author Michal Turek
 */
class AdminController extends BaseAdminController
{
    protected function process(): void
    {
        if (isset($_POST['admin_login_form'])) {
            $this->processAdminLogin();
        }

        if ($this->loggedUser === null) {
            return;
        }

        $currentYear = $this->getDatabase()->getOption(Options::YEAR);
        $currentSemester = $this->getDatabase()->getOption(Options::SEMESTER);
        if (!is_numeric($currentYear) || !is_numeric($currentSemester)) {
            $this->templateData['action'] = 'error';
            return;
        }
        $currentSemester = (int) $currentSemester === 1 ? Semester::SUMMER : Semester::WINTER;

        if (isset($_GET['subject']) && is_numeric($_GET['subject'])) {
            $this->actionDetail();
        } else {
            $this->actionDefault((int) $currentYear, $currentSemester);
        }
        $this->templateData['currentYear'] = $currentYear;
        $this->templateData['currentSemester'] = $currentSemester;
    }

    // AKCE

    /**
     * Výchozí akce přihlášeného uživatele, zobrazí seznam dostupných předmětů.
     *
     * @param int $currentYear aktuální akademický rok
     * @param Semester $currentSemester aktuální semestr
     */
    private function actionDefault(int $currentYear, Semester $currentSemester): void
    {
        $this->templateData['subjects'] = $this->getDatabase()->getSubjectsByTeacher($this->loggedUser->id, $currentYear, $currentSemester);
    }

    /**
     * Akce detailu předmětu, zobrazí všechny rozvrhové akce, ke kterým má přihlášený uživatel přístup.
     */
    private function actionDetail(): void
    {
        $subject = $this->getDatabase()->getSubjectById((int) $_GET['subject']);
        if ($subject === null) {
            $this->error404();
        }

        $events = $this->getDatabase()->getScheduledEventsByTeacherAndSubject($this->loggedUser->id, (int)$_GET['subject']);

        if (empty($events)) {
            $this->error404();
        }

        $this->templateData['events'] = $events;
        $this->templateData['subject'] = $subject;
    }

    // FORMULÁŘE

    /**
     * Metoda pro zpracování přihlašovacího formuláře.
     */
    private function processAdminLogin(): void
    {
        if (!isset($_POST['username'], $_POST['password'])) {
            $this->alertMessage('danger', 'Zadejte uživatelské jméno i heslo');
            return;
        }

        $admin = $this->getDatabase()->getAdminUserByNameAndTestAuthentication($_POST['username'], $_POST['password']);
        if ($admin === null) {
            $this->alertMessage('danger', 'Uživatelské jméno nebo heslo není platné');
            $this->redirect('admin');
        }

        $this->getSession()->set(Session::ADMIN, $admin->id);
        $this->getDatabase()->log('Uživatel se přihlásil', LogType::LOGIN, userId: $admin->id);
        $this->alertMessage('success', 'Úspěšně přihlášeno');

        $this->redirect('admin');
    }
}
