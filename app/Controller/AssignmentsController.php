<?php

declare(strict_types=1);

namespace App\Controller;

use App\Model\AssignmentManager;
use App\Model\Database\Entities\Assignment;
use App\Model\Database\Entities\Student;
use App\Model\Database\Types\FileType;
use App\Model\Database\Types\LogType;
use App\Model\Database\Types\Options;
use App\Model\Session;
use App\Model\AutomaticCheckManager;
use DateTime;

/**
 * Controller sloužící pro prohlížení zadání pro daného studenta a odevzdávání vypracování.
 *
 * @author Michal Turek
 */
class AssignmentsController extends Controller
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

        $this->templateData['loggedStudent'] = $student;
        $this->templateData['now'] = $now = new DateTime();
        // Pokud je v URL dostupné ID, dojde k zobrazení detailu vybraného zadání
        if (isset($_GET['id']) && is_numeric($_GET['id'])) {
            $id = (int) $_GET['id'];

            $assignment = $this->getDatabase()->getAssignmentById($id);
            $details = $this->getDatabase()->getStudentAssignmentDetails($id, $studentId);
            if (!$assignment || $assignment->dateFrom > $now || !$details || !$details->generated) {
                $this->error404();
                return;
            }

            $action = $_GET['action'] ?? 'detail';
            $showValidatorReportSection = ($action === 'validator-report');

            if ($assignment->dateTo >= $now && isset($_POST['submit_attachment_form'], $_FILES['attachment'])) {
                $this->processSubmitAttachmentForm($assignment, $student);
            }

            // Pokud je v URL dostupná hodnota file, dojde ke stažení konkrétního souboru z daného zadání. Musí se jednat o soubor se zadáním nebo náhledem.
            if (isset($_GET['file']) && is_numeric($_GET['file'])) {
                $file = $this->getDatabase()->getAssignmentFileById((int) $_GET['file']);
                if (!$file || $file->assignmentId !== $assignment->id || $file->studentId !== $student->id || !in_array($file->filetype, [FileType::INPUT, FileType::ASSIGNMENT_TXT, FileType::PREVIEW])) {
                    $this->error404();
                    return;
                }

                $this->getDatabase()->log('Student stáhnul soubor ' . $file->filename . ' zadání ' . $assignment->name, LogType::DOWNLOAD, studentId: $student->id);
                (new AssignmentManager($this->getDatabase()))->downloadFile($file);
            }

            $this->templateData['assignment'] = $assignment;
            $this->templateData['details'] = $details;
            $files = $this->getDatabase()->getStudentAssignmentFiles($id, $studentId, true);
            foreach ($files as $file) {
                if ($file->filetype === FileType::ASSIGNMENT_TXT) {
                    $this->templateData['assignmentText'] = file_get_contents(DOCUMENT_FOLDER . '/' . $file->studentId . '/' . $file->assignmentId . '/' . $file->location);
                    break;
                }
            }
            $this->templateData['files'] = $files;
            $automaticCheckManager = new AutomaticCheckManager($this->getDatabase());
            $reportData = $automaticCheckManager->buildStudentReportData(
                $assignment,
                $student,
            );

            $this->templateData['canShowValidatorReport'] = $reportData['canShowValidatorReport'];
            $this->templateData['showValidatorReportSection'] = $showValidatorReportSection;
            $this->templateData['checkerReport'] = $reportData['checkerReport'];
            $this->templateData['studentViewMinPenalty'] = $reportData['studentViewMinPenalty'];
            $this->templateData['finalPoints'] = $reportData['finalPoints'];
            $this->templateData['attempts'] = $this->getDatabase()->countStudentAttempts($id, $studentId);
        } else {
            // výchozí akce výpisu všech zadání
            $this->templateData['assignments'] = $this->getDatabase()->getPublishedStudentAssignments($studentId);
        }
    }

    // FORMULÁŘE    
    /**
     * Metoda slouží pro zpracování formuláře na odevzdání souboru s vypracováním.
     *
     * @param Assignment $assignment zadání
     * @param Student $student přihlášený student
     */
    public function processSubmitAttachmentForm(Assignment $assignment, Student $student): void
    {
        if (!isset($_FILES['attachment']['name'], $_FILES['attachment']['tmp_name']) || !is_string($_FILES['attachment']['name']) || !is_string($_FILES['attachment']['tmp_name'])) {
            $this->alertMessage('danger', 'Nahrajte právě jeden soubor!');
            return;
        }

        $manager = new AssignmentManager($this->getDatabase());
        if ($manager->uploadFile($assignment->id, $student, $_FILES['attachment']) === false) {
            $this->alertMessage('danger', 'Soubor se nepodařilo nahrát!');
            return;
        }
        // Author Adam Vaněček
        try {
            $automaticCheckManager = new AutomaticCheckManager($this->getDatabase());
            $automaticCheckManager->enqueueCheck($assignment, $student);

            $this->getDatabase()->log(
                "Automatická kontrola byla zařazena do fronty (zadání ID={$assignment->id}).",
                LogType::SUBMIT,
                studentId: $student->id
            );
        } catch (\Throwable $e) {
            $this->getDatabase()->log(
                "CHYBA automatické kontroly (zadání ID={$assignment->id}): " . $e->getMessage(),
                LogType::SUBMIT,
                studentId: $student->id
            );
        }
        // Author Adam Vaněček
        $this->getDatabase()->log('Student odevzdal soubor ' . $_FILES['attachment']['name'] . ' do zadání ' . $assignment->name, LogType::SUBMIT, studentId: $student->id);
        $this->alertMessage('success', 'Soubor byl úspěšně odevzdán!');
        $this->redirect('assignments', ['id' => $assignment->id]);
    }
}
