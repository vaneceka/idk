<?php

declare(strict_types=1);

namespace App\Controller;

use App\Model\Database\Types\LogType;
use App\Model\Database\Types\Options;
use App\Model\Session;

/**
 * Controller sloužící k odhlášení přihlášeného studenta.
 * Po odhlášení je přesměrován zpět na {@link HomeController}.
 *
 * @author Michal Turek
 */
class LogoutController extends Controller
{
    protected function process(): void
    {
        $studentId = $this->getSession()->get(Session::STUDENT);
        if (!$studentId) {
            $this->redirect('home');
        }

        $currentYear = $this->getDatabase()->getOption(Options::YEAR);
        $currentSemester = $this->getDatabase()->getOption(Options::SEMESTER);
        if (!is_numeric($currentYear) || !is_numeric($currentSemester)) {
            return;
        }

        $student = $this->getDatabase()->getStudentById($studentId);
        if (!$student) {
            $this->getSession()->delete(Session::STUDENT);
            $this->redirect('home');
        }

        if ($student !== null) {
            $this->getSession()->delete(Session::STUDENT);
            $this->getDatabase()->log('Uživatel se odhlásil', LogType::LOGOUT, studentId: $student->id);
            $this->alertMessage('success', 'Úspěšně odhlášeno');
        }
        $this->redirect('home');
    }
}
