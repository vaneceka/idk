<?php

declare(strict_types=1);

namespace App\Model;

use App\Model\Database\DatabaseManager;
use App\Model\Database\Entities\Assignment;
use App\Model\Database\Entities\Student;
use App\Model\Database\Types\FileType;

/**
 * Třída zajišťuje spuštění automatické kontroly a načtení jejích výstupů.
 *
 * @author Adam Vaněček
 */
class AutomaticCheckManager
{
    public function __construct(
        private readonly DatabaseManager $database,
    ) {
    }

    /**
     * Připraví soubory a zařadí automatickou kontrolu do fronty.
     *
     * @param Assignment $assignment zadání
     * @param Student $student student
     * @return void
     */
    public function enqueueCheck(Assignment $assignment, Student $student): void
    {
        $studentDir = $this->ensureStudentDir($student, $assignment);
        $logFile = $this->ensureCheckerLogFile($assignment, $student, $studentDir);
        $configPath = $this->writeChecksConfig($assignment, $studentDir);
        $this->runChecker($studentDir, $configPath, $logFile);
    }

    /**
     * Vrátí data pro zobrazení checker reportu studentovi.
     *
     * @param Assignment $assignment zadání
     * @param Student $student student
     * @return array{canShowValidatorReport: bool, studentViewMinPenalty: int, checkerReport: ?array, finalPoints: int}
     */
    public function buildStudentReportData(Assignment $assignment, Student $student): array
    {
        $dbCfg = $this->database->getChecksConfigByAssignmentId($assignment->id) ?? [];
        $studentViewCfg = is_array($dbCfg['student_view'] ?? null) ? $dbCfg['student_view'] : [];

        $canShowValidatorReport = (bool)($studentViewCfg['enabled'] ?? false);
        $studentViewMinPenalty = abs((int)($studentViewCfg['min_penalty'] ?? 100));

        $checkerReport = null;
        $checkerManager = new CheckerReportManager();

        $allFiles = $this->database->getStudentAssignmentFiles($assignment->id, $student->id);
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

        $finalPoints = 100;
        if ($checkerReport && isset($checkerReport['total_penalty'])) {
            $penalty = (int)$checkerReport['total_penalty'];
            
            $finalPoints = max(0, 100 + $penalty);

            $checkerReport['total_penalty'] = max($penalty, -100);
        }

        return [
            'canShowValidatorReport' => $canShowValidatorReport,
            'studentViewMinPenalty' => $studentViewMinPenalty,
            'checkerReport' => $checkerReport,
            'finalPoints' => $finalPoints, 
        ];
    }

    /**
     * Zajistí existenci studentské složky.
     *
     * @param Student $student student
     * @param Assignment $assignment zadání
     * @return string
     */
    private function ensureStudentDir(Student $student, Assignment $assignment): string
    {
        $studentDir = DOCUMENT_FOLDER . '/' . $student->id . '/' . $assignment->id;

        if (!is_dir($studentDir)) {
            if (!mkdir($studentDir, 0775, true) && !is_dir($studentDir)) {
                throw new \RuntimeException("Nelze vytvořit složku: {$studentDir}");
            }
        }

        if (!is_writable($studentDir)) {
            throw new \RuntimeException("Složka není zapisovatelná: {$studentDir}");
        }

        return $studentDir;
    }

    /**
     * Zajistí existenci logu automatické kontroly a jeho evidenci v databázi.
     *
     * @param Assignment $assignment zadání
     * @param Student $student student
     * @param string $studentDir studentská složka
     * @return string
     */
    private function ensureCheckerLogFile(Assignment $assignment, Student $student, string $studentDir): string
    {
        $logFile = $studentDir . '/automaticka_kontrola.log';

        if (!is_file($logFile)) {
            if (@touch($logFile) === false) {
                throw new \RuntimeException("Nelze vytvořit log soubor: {$logFile}");
            }
        }

        $existingFiles = $this->database->getStudentAssignmentFiles($assignment->id, $student->id);

        $logExistsInDb = false;
        foreach ($existingFiles as $file) {
            if (
                $file->filetype === FileType::CHECKER_LOG &&
                $file->filename === 'automaticka_kontrola.log'
            ) {
                $logExistsInDb = true;
                break;
            }
        }

        if (!$logExistsInDb) {
            $result = $this->database->addAssignmentFile(
                $assignment->id,
                $student->id,
                'automaticka_kontrola.log',
                FileType::CHECKER_LOG,
                'automaticka_kontrola.log'
            );

            if ($result === false) {
                throw new \RuntimeException('Nepodařilo se uložit checker log do databáze.');
            }
        }

        return $logFile;
    }

    /**
     * Vytvoří konfigurační JSON pro checker.
     *
     * @param Assignment $assignment zadání
     * @param string $studentDir studentská složka
     * @return string
     */
    private function writeChecksConfig(Assignment $assignment, string $studentDir): string
    {
        $configManager = new ChecksConfigManager();

        $dbCfg = $this->database->getChecksConfigByAssignmentId($assignment->id) ?? [];
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

        return $configPath;
    }

    /**
     * Spustí checker nad studentskou složkou.
     *
     * @param string $studentDir studentská složka
     * @param string $configPath cesta ke konfiguraci
     * @param string $logFile cesta k logu
     * @return void
     */
    private function runChecker(string $studentDir, string $configPath, string $logFile): void
    {
        if (!defined('CHECKER_WORKDIR')) {
            define('CHECKER_WORKDIR', '/checker');
        }

        $runner = CHECKER_WORKDIR . '/bin/run_checker.sh';
        $cmd = 'cd ' . escapeshellarg(CHECKER_WORKDIR) . ' && ' .
            escapeshellcmd($runner) .
            ' --student-dir ' . escapeshellarg($studentDir) .
            ' --out-dir ' . escapeshellarg($studentDir) .
            ' --output ' . escapeshellarg('json') .
            ' --checks-config ' . escapeshellarg($configPath) .
            ' >> ' . escapeshellarg($logFile) . ' 2>&1 &';

        exec($cmd);
    }
}