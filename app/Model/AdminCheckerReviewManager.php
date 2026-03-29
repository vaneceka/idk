<?php

declare(strict_types=1);

namespace App\Model;

use App\Model\Database\DatabaseManager;
use App\Model\Database\Types\FileType;

/**
 * Manager pro načítání a správu dat automatické kontroly v detailu zadání studenta.
 *
 * @author Adam Vaněček
 */
class AdminCheckerReviewManager
{
    public function __construct(
        private readonly DatabaseManager $database,
    ) {
    }

    /**
     * Připraví data automatické kontroly pro detail zadání studenta.
     *
     * @param int $assignmentId ID zadání
     * @param int $studentId ID studenta
     * @return array
     */
    public function buildAssignmentDetailData(int $assignmentId, int $studentId): array
    {
        $checkerManager = new CheckerReportManager();
        $files = $this->database->getStudentAssignmentFiles($assignmentId, $studentId);

        $uploads = $this->getSortedUploads($files, $checkerManager);
        $latestUpload = $uploads[0] ?? null;
        $latestTime = $latestUpload ? $checkerManager->timeToTs($latestUpload->time) : 0;

        $baseDir = $checkerManager->getBaseDir($studentId, $assignmentId);
        $primaryPath = $baseDir . '/primary.json';

        $checkerManager->ensurePrimaryIsFresh($baseDir, $primaryPath, $latestUpload, $latestTime);

        $primaryUpload = $checkerManager->resolvePrimaryUpload($uploads, $primaryPath);
        $uploadPenalties = $checkerManager->buildUploadPenalties($baseDir, $uploads);

        $checkerReport = null;
        if ($primaryUpload) {
            $reportPath = $checkerManager->findReportForUpload(
                $baseDir,
                $primaryUpload->filename,
                $primaryUpload->time
            );

            $checkerReport = $checkerManager->loadCheckerReport($reportPath);
        }

        $suggestedComment = $checkerManager->buildSuggestedComment($checkerReport);

        return [
            'files' => $files,
            'uploads' => $uploads,
            'baseDir' => $baseDir,
            'primaryPath' => $primaryPath,
            'primaryUpload' => $primaryUpload,
            'uploadPenalties' => $uploadPenalties,
            'checkerReport' => $checkerReport,
            'suggestedComment' => $suggestedComment,
        ];
    }

    /**
     * Nastaví primární upload pro checker.
     *
     * @param int $assignmentId ID zadání
     * @param int $studentId ID studenta
     * @param int $setPrimaryId ID uploadu, který se má nastavit jako primární
     * @return bool true při úspěchu, jinak false
     */
    public function setPrimaryUpload(int $assignmentId, int $studentId, int $setPrimaryId): bool
    {
        if ($setPrimaryId <= 0) {
            return false;
        }

        $checkerManager = new CheckerReportManager();
        $files = $this->database->getStudentAssignmentFiles($assignmentId, $studentId);
        $uploads = $this->getSortedUploads($files, $checkerManager);

        $latestUpload = $uploads[0] ?? null;
        $latestTime = $latestUpload ? $checkerManager->timeToTs($latestUpload->time) : 0;

        $baseDir = $checkerManager->getBaseDir($studentId, $assignmentId);
        $primaryPath = $baseDir . '/primary.json';

        $target = null;
        foreach ($uploads as $upload) {
            if ((int)$upload->id === $setPrimaryId) {
                $target = $upload;
                break;
            }
        }

        if ($target === null) {
            return false;
        }

        $checkerManager->writePrimary($baseDir, $primaryPath, $target, $latestTime, true);
        return true;
    }

    /**
     * Zpracuje ignorování checker chyb.
     *
     * @param int $assignmentId ID zadání
     * @param int $studentId ID studenta
     * @param array $post odeslaná data formuláře
     * @return bool true pokud došlo k uložení
     */
    public function handleIgnoreSubmit(int $assignmentId, int $studentId, array $post): bool
    {
        if (!isset($post['checker_ignore_form'])) {
            return false;
        }

        $checkerManager = new CheckerReportManager();
        $data = $this->buildAssignmentDetailData($assignmentId, $studentId);
        $primaryUpload = $data['primaryUpload'];

        if ($primaryUpload === null) {
            return false;
        }

        $reportPath = $checkerManager->findReportForUpload(
            $data['baseDir'],
            $primaryUpload->filename,
            $primaryUpload->time
        );

        if (!$reportPath || !is_file($reportPath)) {
            return false;
        }

        return $checkerManager->applyCheckerIgnoresToReport($reportPath, $post);
    }

    /**
     * Vrátí uploady seřazené od nejnovějšího.
     *
     * @param array $files soubory zadání
     * @param CheckerReportManager $checkerManager manager checker reportů
     * @return array
     */
    private function getSortedUploads(array $files, CheckerReportManager $checkerManager): array
    {
        $uploads = array_values(array_filter(
            $files,
            fn($file) => $file->filetype === FileType::UPLOAD
        ));

        usort(
            $uploads,
            fn($a, $b) => $checkerManager->timeToTs($b->time) <=> $checkerManager->timeToTs($a->time)
        );

        return $uploads;
    }
}