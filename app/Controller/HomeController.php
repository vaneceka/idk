<?php

declare(strict_types=1);

namespace App\Controller;

use App\Model\Database\Types\LogType;
use App\Model\Database\Types\Options;
use App\Model\Database\Types\Semester;
use App\Model\Session;

/**
 * Výchozí controller aplikace, obsahuje přihlašovací formulář pro studenty.
 * Přihlášený student je přesměrován na {@link AssignmentsController}.
 *
 * @author Michal Turek
 */
class HomeController extends Controller
{
    protected function process(): void
    {
        $studentId = $this->getSession()->get(Session::STUDENT);
        if ($studentId) {
            $this->redirect('assignments');
            return;
        }

        if (isset($_POST['login_form'])) {
            $this->processLogin();
        }
    }

    // FORMULÁŘE

    /**
     * Metoda pro zpracování přihlašovacího formuláře studenta.
     */
    private function processLogin(): void
    {
        $currentYear = $this->getDatabase()->getOption(Options::YEAR);
        $currentSemester = $this->getDatabase()->getOption(Options::SEMESTER);
        if (!is_numeric($currentYear) || !is_numeric($currentSemester)) {
            return;
        }

        if (!isset($_POST['username'], $_POST['password'])) {
            $this->alertMessage('danger', 'Zadejte uživatelské jméno i heslo');
            return;
        }

        $student = $this->getDatabase()->getStudentByOrionAndStudentNumber($_POST['username'], $_POST['password'], (int) $currentYear, $currentSemester == 1 ? Semester::SUMMER : Semester::WINTER);
        if ($student === null) {
            $this->alertMessage('danger', 'Uživatelské jméno nebo heslo není platné');
            $this->redirect('home');
        }

        $this->getSession()->set(Session::STUDENT, $student->id);
        $this->getDatabase()->log('Uživatel se přihlásil', LogType::LOGIN, studentId: $student->id);
        $this->alertMessage('success', 'Úspěšně přihlášeno');

        $this->redirect('assignments');
    }
}
