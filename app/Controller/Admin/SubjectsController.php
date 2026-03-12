<?php

declare(strict_types=1);

namespace App\Controller\Admin;

use App\Model\Database\Entities\ScheduledEvent;
use App\Model\Database\Entities\Subject;
use App\Model\Database\Types\LogType;
use App\Model\Database\Types\Options;
use App\Model\Database\Types\Semester;

/**
 * Controller sloužící pro správu předmětů a rozvrhových akcí.
 *
 * @author Michal Turek
 */
class SubjectsController extends BaseAdminController
{
    /**
     * Aktuální akademický rok
     *
     * @var int
     */
    private int $currentYear;
    /**
     * Aktuální semestr
     *
     * @var Semester
     */
    private Semester $currentSemester;

    protected function process(): void
    {
        if (!$this->loggedUser->isAdmin) {
            $this->error404();
            return;
        }

        $currentYear = $this->getDatabase()->getOption(Options::YEAR);
        $currentSemester = $this->getDatabase()->getOption(Options::SEMESTER);
        if (!is_numeric($currentYear) || !is_numeric($currentSemester)) {
            $this->templateData['action'] = 'error';
            return;
        }
        $this->currentYear = (int) $currentYear;
        $this->currentSemester = (int) $currentSemester === 1 ? Semester::SUMMER : Semester::WINTER;

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
            case 'events':
                $this->actionEvents();
                break;
            case 'add-event':
                $this->actionAddEvent();
                break;
            case 'edit-event':
                $this->actionEditEvent();
                break;
            default:
                $this->error404();
                return;
        }
        $this->templateData['action'] = $action;
        $this->templateData['currentYear'] = $currentYear;
        $this->templateData['currentSemester'] = $this->currentSemester;
    }

    // AKCE

    /**
     * Výchozí akce pro výpis předmětů. Vypsané předměty se řídí aktuálním akademickým rokem a semestrem v globálním nastavení systému.
     */
    private function actionDefault(): void
    {
        $this->templateData['subjects'] = $this->getDatabase()->getSubjectsByYearAndSemester($this->currentYear, $this->currentSemester);
    }

    /**
     * Akce pro přidání nového předmětu.
     */
    private function actionAdd(): void
    {
        if (isset($_POST['admin_subjects_add_form'])) {
            $this->processSubjectAddForm();
        }
    }

    /**
     * Akce pro úpravu existujícího předmětu.
     */
    private function actionEdit(): void
    {
        if (!isset($_GET['id'])) {
            $this->error404();
            return;
        }

        $id = (int) $_GET['id'];
        $subject = $this->getDatabase()->getSubjectById($id);
        if (!$subject) {
            $this->error404();
            return;
        }

        if (isset($_POST['admin_subjects_edit_form'])) {
            $this->processSubjectEditForm($subject);
        } else {
            $this->templateData['post'] = [
                'name' => $subject->name,
                'shortcut' => $subject->shortcut,
            ];
        }
    }

    /**
     * Akce pro výpis všech rozvrhových akcí součástí jednoho předmětu.
     */
    private function actionEvents(): void
    {
        if (!isset($_GET['id'])) {
            $this->error404();
            return;
        }

        $id = (int) $_GET['id'];
        $subject = $this->getDatabase()->getSubjectById($id);
        if (!$subject) {
            $this->error404();
            return;
        }

        $this->templateData['subject'] = $subject;
        $this->templateData['events'] = $this->getDatabase()->getScheduledEventsBySubject($id);
    }

    /**
     * Akce pro přidání nové rozvrhové akce nebo zápočtového termínu pro konkrétní předmět.
     */
    private function actionAddEvent(): void
    {
        if (!isset($_GET['id'])) {
            $this->error404();
            return;
        }

        $id = (int) $_GET['id'];
        $subject = $this->getDatabase()->getSubjectById($id);
        if (!$subject) {
            $this->error404();
            return;
        }
        $this->templateData['teachers'] = $this->getDatabase()->getAllAdminUsers();

        $this->templateData['subject'] = $subject;

        if (isset($_POST['admin_subjects_event_add_form'])) {
            $this->processSubjectAddEventForm($subject);
        }
    }

    /**
     * Akce pro úpravu existující rozvrhové akce nebo zápočtového termínu.
     */
    private function actionEditEvent(): void
    {
        if (!isset($_GET['id'])) {
            $this->error404();
            return;
        }

        $id = (int) $_GET['id'];
        $event = $this->getDatabase()->getScheduledEventById($id);
        if (!$event) {
            $this->error404();
            return;
        }
        $this->templateData['teachers'] = $this->getDatabase()->getAllAdminUsers();

        $subject = $this->getDatabase()->getSubjectById($event->subjectId);
        $this->templateData['subject'] = $subject;

        if (isset($_POST['admin_subjects_event_edit_form'])) {
            $this->processSubjectEditEventForm($subject, $event);
        } else {
            $this->templateData['post'] = [
                'day' => $event->day,
                'timeFrom' => $event->timeFrom,
                'timeTo' => $event->timeTo,
                'teachers' => $this->getDatabase()->getTeacherIdsByScheduledEvent($event->id),
                'type' => $event->isExam ? 'exam' : 'regular',
                'day_exam' => $event->examDate?->format('Y-m-d') ?? null,
            ];
        }
    }

    // FORMULÁŘE

    /**
     * Metoda pro zpracování formuláře na vytvoření nového předmětu.
     * Předmět je vždy vytvořen do aktuálního akademického roku a semestru podle globálního nastavení systému.
     */
    private function processSubjectAddForm(): void
    {
        $post = [];

        $missing = false;

        if (isset($_POST['name'])) {
            $post['name'] = $_POST['name'];
        } else {
            $missing = true;
        }

        if (isset($_POST['shortcut'])) {
            $post['shortcut'] = $_POST['shortcut'];
        } else {
            $missing = true;
        }

        if ($missing) {
            $this->alertMessage('danger', 'Nejsou vyplněna všechna požadovaná pole');
            return;
        }

        $subjectId = $this->getDatabase()->createSubject($post['shortcut'], $post['name'], $this->currentYear, $this->currentSemester);
        if ($subjectId === false) {
            $this->alertMessage('danger', 'Nepodařilo se vytvořit předmět');
            return;
        }

        $this->getDatabase()->log('Vytvořil nový předmět ' . $post['shortcut'] . ' (Název ' . $post['name'] . '; ID ' . $subjectId . '; Rok ' . $this->currentYear . '; Semestr ' . $this->currentSemester->getName(). ')', LogType::SUBJECT_ADD, userId: $this->loggedUser->id);
        $this->alertMessage('success', 'Předmět byl úspěšně vytvořen');
        $this->redirect('admin/subjects');
    }

    /**
     * Metoda pro zpracování formuláře na úpravu předmětu.
     *
     * @param Subject $subject upravovaný předmět
     */
    private function processSubjectEditForm(Subject $subject): void
    {
        $post = [];

        $missing = false;

        if (isset($_POST['name'])) {
            $post['name'] = $_POST['name'];
        } else {
            $missing = true;
        }

        if (isset($_POST['shortcut'])) {
            $post['shortcut'] = $_POST['shortcut'];
        } else {
            $missing = true;
        }

        $this->templateData['post'] = $post;

        if ($missing) {
            $this->alertMessage('danger', 'Nejsou vyplněna všechna požadovaná pole');
            return;
        }

        $result = $this->getDatabase()->updateSubject($subject->id, $post['shortcut'], $post['name']);
        if ($result === false) {
            $this->alertMessage('danger', 'Nepodařilo se upravit předmět');
            return;
        }

        $this->getDatabase()->log('Upraven předmět ' . $post['shortcut'] . ' (Název ' . $post['name'] . '; ID ' . $subject->id . '; Rok ' . $subject->year . '; Semestr ' . $subject->semester->getName(). ')', LogType::SUBJECT_EDIT, userId: $this->loggedUser->id);
        $this->alertMessage('success', 'Předmět byl úspěšně upraven');
        $this->redirect('admin/subjects');
    }

    /**
     * Metoda pro zpracování formuláře na přidání nové rozvrhové akce.
     *
     * @param Subject $subject předmět, do kterého se rozvrhová akce přidává.
     */
    private function processSubjectAddEventForm(Subject $subject): void
    {
        $post = [];

        $missing = false;

        $type = 'regular';
        if (isset($_POST['type']) && $_POST['type'] === 'exam') {
            $type = 'exam';
        }

        if ($type === 'regular') {
            if (isset($_POST['day'])) {
                $post['day'] = $_POST['day'];
            } else {
                $missing = true;
            }
        } else {
            if (isset($_POST['day_exam'])) {
                $post['day_exam'] = $_POST['day_exam'];
            } else {
                $missing = true;
            }
        }

        if (isset($_POST['timeFrom'])) {
            $post['timeFrom'] = $_POST['timeFrom'];
        } else {
            $missing = true;
        }

        if (isset($_POST['timeTo'])) {
            $post['timeTo'] = $_POST['timeTo'];
        } else {
            $missing = true;
        }

        if (isset($_POST['teachers']) && is_array($_POST['teachers'])) {
            $post['teachers'] = $_POST['teachers'];
        }

        $this->templateData['post'] = $post;

        if ($missing) {
            $this->alertMessage('danger', 'Nejsou vyplněna všechna požadovaná pole');
            return;
        }

        if ($type === 'regular') {
            if (!is_numeric($post['day']) || (int)$post['day'] < 1 || (int)$post['day'] > 7) {
                $this->alertMessage('danger', 'Den musí být číslo od 1 do 7');
                return;
            }
        } else {
            $day = \DateTime::createFromFormat('Y-m-d', $post['day_exam']);
            if ($day === false) {
                $this->alertMessage('danger', 'Datum nebyl poslán v požadovaném formátu');
                return;
            }
        }

        if (!preg_match("/^(?:2[0-3]|[01][0-9]):[0-5][0-9]$/", $post['timeFrom'])) {
            $this->alertMessage('danger', 'Čas od musí být ve formátu HH:MM');
            return;
        }

        if (!preg_match("/^(?:2[0-3]|[01][0-9]):[0-5][0-9]$/", $post['timeTo'])) {
            $this->alertMessage('danger', 'Čas do musí být ve formátu HH:MM');
            return;
        }

        if ($post['timeFrom'] > $post['timeTo']) {
            $this->alertMessage('danger', 'Čas do musí být větší než čas od');
            return;
        }

        $eventId = $this->getDatabase()->createScheduledEvent($subject->id, (int) ($post['day'] ?? 1), $post['timeFrom'], $post['timeTo'], $day ?? null);
        if ($eventId === false) {
            $this->alertMessage('danger', 'Nepodařilo se vytvořit rozvrhovou akci');
            return;
        }
        $this->getDatabase()->updateTeachers($eventId, $post['teachers']);

        if ($type === 'regular') {
            $this->getDatabase()->log('Vytvořil novou rozvrhovou akci pro předmět ' . $subject->shortcut . ' (Čas ' . $post['timeFrom'] . ' - ' . $post['timeTo'] . '; Den ' . $post['day'] . '; ID ' . $eventId . '; Vyučující ' . implode(', ', $post['teachers']) . ')', LogType::EVENT_ADD, userId: $this->loggedUser->id);
        } else {
            $this->getDatabase()->log('Vytvořil nový zkouškový termín pro předmět ' . $subject->shortcut . ' (Čas ' . $post['timeFrom'] . ' - ' . $post['timeTo'] . '; Den ' . $day->format('j. n. Y') . '; ID ' . $eventId . '; Vyučující ' . implode(', ', $post['teachers']) . ')', LogType::EVENT_ADD, userId: $this->loggedUser->id);
        }
        $this->alertMessage('success', 'Rozvrhová akce byla úspěšně vytvořena');
        $this->redirect('admin/subjects', ['action' => 'events', 'id' => $subject->id]);
    }

    /**
     * Metoda pro zpracování formuláře na úpravu rozvrhové akce.
     *
     * @param Subject $subject předmět, kterého je rozvrhová akce součástí
     * @param ScheduledEvent $event upravovaná rozvrhová akce
     */
    private function processSubjectEditEventForm(Subject $subject, ScheduledEvent $event): void
    {
        $post = [];

        $missing = false;

        $type = 'regular';
        if (isset($_POST['type']) && $_POST['type'] === 'exam') {
            $type = 'exam';
        }

        if ($type === 'regular') {
            if (isset($_POST['day'])) {
                $post['day'] = $_POST['day'];
            } else {
                $missing = true;
            }
        } else {
            if (isset($_POST['day_exam'])) {
                $post['day_exam'] = $_POST['day_exam'];
            } else {
                $missing = true;
            }
        }

        if (isset($_POST['timeFrom'])) {
            $post['timeFrom'] = $_POST['timeFrom'];
        } else {
            $missing = true;
        }

        if (isset($_POST['timeTo'])) {
            $post['timeTo'] = $_POST['timeTo'];
        } else {
            $missing = true;
        }

        if (isset($_POST['teachers']) && is_array($_POST['teachers'])) {
            $post['teachers'] = $_POST['teachers'];
        } else {
            $post['teachers'] = [];
        }

        $this->templateData['post'] = $post;

        if ($missing) {
            $this->alertMessage('danger', 'Nejsou vyplněna všechna požadovaná pole');
            return;
        }

        if ($type === 'regular') {
            if (!is_numeric($post['day']) || (int)$post['day'] < 1 || (int)$post['day'] > 7) {
                $this->alertMessage('danger', 'Den musí být číslo od 1 do 7');
                return;
            }
        } else {
            $day = \DateTime::createFromFormat('Y-m-d', $post['day_exam']);
            if ($day === false) {
                $this->alertMessage('danger', 'Datum nebyl poslán v požadovaném formátu');
                return;
            }
        }

        if (!preg_match("/^(?:2[0-3]|[01][0-9]):[0-5][0-9]$/", $post['timeFrom'])) {
            $this->alertMessage('danger', 'Čas od musí být ve formátu HH:MM');
            return;
        }

        if (!preg_match("/^(?:2[0-3]|[01][0-9]):[0-5][0-9]$/", $post['timeTo'])) {
            $this->alertMessage('danger', 'Čas do musí být ve formátu HH:MM');
            return;
        }

        if ($post['timeFrom'] > $post['timeTo']) {
            $this->alertMessage('danger', 'Čas do musí být větší než čas od');
            return;
        }

        $result = $this->getDatabase()->updateScheduledEvent($event->id, (int) ($post['day'] ?? 1), $post['timeFrom'], $post['timeTo'], $day ?? null);
        if ($result === false) {
            $this->alertMessage('danger', 'Nepodařilo se upravit rozvrhovou akci');
            return;
        }
        $this->getDatabase()->updateTeachers($event->id, $post['teachers']);

        if ($type === 'regular') {
            $this->getDatabase()->log('Upravil rozvrhovou akci pro předmět ' . $subject->shortcut . ' (Čas ' . $post['timeFrom'] . ' - ' . $post['timeTo'] . '; Den ' . $post['day'] . '; ID ' . $event->id . '; Vyučující ' . implode(', ', $post['teachers']) . ')', LogType::EVENT_EDIT, userId: $this->loggedUser->id);
        } else {
            $this->getDatabase()->log('Upravil zkouškový termín pro předmět ' . $subject->shortcut . ' (Čas ' . $post['timeFrom'] . ' - ' . $post['timeTo'] . '; Den ' . $day->format('j. n. Y') . '; ID ' . $event->id . '; Vyučující ' . implode(', ', $post['teachers']) . ')', LogType::EVENT_EDIT, userId: $this->loggedUser->id);
        }
        $this->alertMessage('success', 'Rozvrhová akce byla úspěšně vytvořena');
        $this->redirect('admin/subjects', ['action' => 'events', 'id' => $subject->id]);
    }
}
