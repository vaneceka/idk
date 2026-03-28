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
use App\Model\CheckerReportManager;
use App\Model\ChecksConfigManager;
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
            $allFiles = $this->getDatabase()->getStudentAssignmentFiles($id, $studentId) ?? [];
            foreach ($files as $file) {
                if ($file->filetype === FileType::ASSIGNMENT_TXT) {
                    $this->templateData['assignmentText'] = file_get_contents(DOCUMENT_FOLDER . '/' . $file->studentId . '/' . $file->assignmentId . '/' . $file->location);
                    break;
                }
            }
            $this->templateData['files'] = $files;

            $dbCfg = $this->getDatabase()->getChecksConfigByAssignmentId($assignment->id) ?? [];
            $studentViewCfg = is_array($dbCfg['student_view'] ?? null) ? $dbCfg['student_view'] : [];
            $canShowValidatorReport = (bool)($studentViewCfg['enabled'] ?? false);
            $studentViewMinPenalty = abs((int)($studentViewCfg['min_penalty'] ?? 100));
            
            $checkerReport = null;
            $checkerManager = new CheckerReportManager();

            $baseDir = $checkerManager->getBaseDir($student->id, $assignment->id);

            $uploads = array_values(array_filter($allFiles, fn($f) => $f->filetype === FileType::UPLOAD));
            usort($uploads, fn($a, $b) => $checkerManager->timeToTs($b->time) <=> $checkerManager->timeToTs($a->time));

            $latestUpload = $uploads[0] ?? null;

            if ($latestUpload) {
                $reportPath = $checkerManager->findReportForUpload(
                    $baseDir,
                    $latestUpload->filename,
                    $latestUpload->time
                );

                $checkerReport = $checkerManager->loadCheckerReport($reportPath);
            }

            $this->templateData['canShowValidatorReport'] = $canShowValidatorReport;
            $this->templateData['showValidatorReportSection'] = $showValidatorReportSection;
            $this->templateData['checkerReport'] = $checkerReport;
            $this->templateData['studentViewMinPenalty'] = $studentViewMinPenalty;
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

        try {
            $studentDir = DOCUMENT_FOLDER . '/' . $student->id . '/' . $assignment->id;

            if (!is_dir($studentDir)) {
                if (!mkdir($studentDir, 0775, true) && !is_dir($studentDir)) {
                    throw new \RuntimeException("Nelze vytvořit složku: {$studentDir}");
                }
            }
            
            if (!is_writable($studentDir)) {
                throw new \RuntimeException("Složka není zapisovatelná: {$studentDir}");
            }
            $configManager = new ChecksConfigManager();
            $logFile = $studentDir . '/automaticka_kontrola.log';
            
            $dbCfg = $this->getDatabase()->getChecksConfigByAssignmentId($assignment->id) ?? [];
            $defsText = $configManager->getAllCheckDefinitions('text');
            $defsSheet = $configManager->getAllCheckDefinitions('spreadsheet');
            $defaultTextMap = $configManager->buildDefaultMap($defsText);
            $defaultSheetMap = $configManager->buildDefaultMap($defsSheet);

            $textMap = $configManager->sanitizeEnabledMap($dbCfg['text'] ?? null, $defaultTextMap);
            $sheetMap = $configManager->sanitizeEnabledMap($dbCfg['spreadsheet'] ?? null, $defaultSheetMap);

            $configPath = $studentDir . '/checks_config.json';

            $json = json_encode(
                ['text' => $textMap, 'spreadsheet' => $sheetMap],
                JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT
            );

            if ($json === false) {
                throw new \RuntimeException("Nelze serializovat checks config do JSON.");
            }

            $w = file_put_contents($configPath, $json);
            if ($w === false) {
                $err = error_get_last();
                throw new \RuntimeException("Nelze zapsat configPath: {$configPath}. " . ($err['message'] ?? ''));
            }

            define('CHECKER_WORKDIR', '/checker');

            $runner = CHECKER_WORKDIR . '/bin/run_checker.sh';
            $cmd = 'cd ' . escapeshellarg(CHECKER_WORKDIR) . ' && ' .
                escapeshellcmd($runner) .
                ' --student-dir ' . escapeshellarg($studentDir) .
                ' --out-dir ' . escapeshellarg($studentDir) .
                ' --output ' . escapeshellarg('json') .
                ' --checks-config ' . escapeshellarg($configPath) .
                ' >> ' . escapeshellarg($logFile) . ' 2>&1 &';
            exec($cmd);

            // $runner = CHECKER_WORKDIR . '/bin/run_checker.sh';

            // $cmd = 'cd ' . escapeshellarg(CHECKER_WORKDIR) . ' && ' .
            //     escapeshellcmd($runner) .
            //     ' --student-dir ' . escapeshellarg($studentDir) .
            //     ' --out-dir ' . escapeshellarg($studentDir) .
            //     ' --output ' . escapeshellarg('json') .
            //     ' --checks-config ' . escapeshellarg($configPath) .
            //     ' >> ' . escapeshellarg($logFile) . ' 2>&1 &';

            // exec($cmd);

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
       
        
        $this->getDatabase()->log('Student odevzdal soubor ' . $_FILES['attachment']['name'] . ' do zadání ' . $assignment->name, LogType::SUBMIT, studentId: $student->id);
        $this->alertMessage('success', 'Soubor byl úspěšně odevzdán!');
        $this->redirect('assignments', ['id' => $assignment->id]);
    }
}
