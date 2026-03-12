<?php

declare(strict_types=1);

namespace App\Model;

use App\Generator\TextDocument\TextDocumentGenerator;
use App\Model\Database\DatabaseManager;
use App\Model\Database\Entities\Assignment;
use App\Model\Database\Entities\AssignmentFile;
use App\Model\Database\Entities\AssignmentProfile;
use App\Model\Database\Entities\AssignmentStudent;
use App\Model\Database\Entities\Student;
use App\Model\Database\Types\FileType;
use App\Model\Database\Types\ProfileType;
use ZipArchive;

/**
 * Třída sloužící pro generování souborů zadání a práci s nimi.
 *
 * @author Michal Turek
 */
class AssignmentManager
{
    public function __construct(private readonly DatabaseManager $databaseManager)
    {
    }

    /**
     * Vygeneruje nové zadání pro studenta
     *
     * @param AssignmentStudent $assignmentStudent vazba mezi studentem a zadáním
     * @param Student $student student
     * @param AssignmentProfile $profile profil zadání
     */
    public function generate(AssignmentStudent $assignmentStudent, Student $student, AssignmentProfile $profile): void
    {
        $folder = DOCUMENT_FOLDER . '/' . $assignmentStudent->studentId . '/' . $assignmentStudent->assignmentId;
        @mkdir($folder, recursive: true);
        if ($profile->type === ProfileType::DOCUMENT) {
            // Textový dokument
            $generator = new TextDocumentGenerator($profile->id);
            $generator->loadOptions($profile->options);
            $document = $generator->generate($student->name . ' ' . $student->surname, $student->studentNumber);

            $document->createSourceFile($folder . '/' . $document->identifier . '.docx', 'Word2007');
            $this->databaseManager->addAssignmentFile($assignmentStudent->assignmentId, $assignmentStudent->studentId, $document->identifier . '.docx', FileType::INPUT, $document->identifier . '.docx');

            $document->createSourceFile($folder . '/' . $document->identifier . '.odt', 'ODText');
            $this->databaseManager->addAssignmentFile($assignmentStudent->assignmentId, $assignmentStudent->studentId, $document->identifier . '.odt', FileType::INPUT, $document->identifier . '.odt');

            file_put_contents($folder . '/assignment.json', $document->createJsonDescription());
            $this->databaseManager->addAssignmentFile($assignmentStudent->assignmentId, $assignmentStudent->studentId, 'assignment.json', FileType::ASSIGNMENT_JSON, 'assignment.json');

            file_put_contents($folder . '/zadani.txt', $document->createAssignmentDescription());
            $this->databaseManager->addAssignmentFile($assignmentStudent->assignmentId, $assignmentStudent->studentId, 'zadani.txt', FileType::ASSIGNMENT_TXT, 'zadani.txt');

//            $document->createResultFile($folder . '/result.pdf');
//            $this->databaseManager->addAssignmentFile($assignmentStudent->assignmentId, $assignmentStudent->studentId, 'nahled.pdf', FileType::PREVIEW, 'result.pdf');

            foreach ($document->objects as $object) {
                copy($object->file, $folder . '/' . $object->identifier . '.png');
                $this->databaseManager->addAssignmentFile($assignmentStudent->assignmentId, $assignmentStudent->studentId,  $object->identifier . '.png', FileType::INPUT, $object->identifier . '.png');
            }
        } else {
            // Tabulkový procesor
            $generators = ($profile->options['generators'] ?? ['Bmi', 'BloodPressure', 'Hospitalization']);
            if (!$generators) {
                $generators = ['Bmi'];
            }
            $generator = new ('\App\Generator\Spreadsheet\\' . $generators[rand(0, count($generators) - 1)] . 'SpreadsheetGenerator')();
            $document = $generator->generate($student->studentNumber . '_' . substr(md5(microtime()), rand(0, 26), 5), (int) ($profile->options['min'] ?: 15), (int) ($profile->options['max'] ?: 22));

            $document->createSourceFile($folder . '/' . $document->identifier . '.xlsx', 'Xlsx');
            $this->databaseManager->addAssignmentFile($assignmentStudent->assignmentId, $assignmentStudent->studentId, $document->identifier . '.xlsx', FileType::INPUT, $document->identifier . '.xlsx');

            $document->createSourceFile($folder . '/' . $document->identifier . '.ods', 'Ods');
            $this->databaseManager->addAssignmentFile($assignmentStudent->assignmentId, $assignmentStudent->studentId, $document->identifier . '.ods', FileType::INPUT, $document->identifier . '.ods');

            $document->createSourceFile($folder . '/' . $document->identifier . '-result.pdf', 'Mpdf', true);
            $this->databaseManager->addAssignmentFile($assignmentStudent->assignmentId, $assignmentStudent->studentId, 'nahled.pdf', FileType::PREVIEW, $document->identifier . '-result.pdf');

            file_put_contents($folder . '/assignment.json', $document->createJsonDescription());
            $this->databaseManager->addAssignmentFile($assignmentStudent->assignmentId, $assignmentStudent->studentId, 'assignment.json', FileType::ASSIGNMENT_JSON, 'assignment.json');

            file_put_contents($folder . '/zadani.txt', $document->createAssignmentDescription());
            $this->databaseManager->addAssignmentFile($assignmentStudent->assignmentId, $assignmentStudent->studentId, 'zadani.txt', FileType::ASSIGNMENT_TXT, 'zadani.txt');
        }

        $this->databaseManager->setAssignmentGenerated($assignmentStudent->assignmentId, $assignmentStudent->studentId);
    }

    /**
     * Pošle klientovi soubor zadání a ukončí vykonávání programu.
     *
     * @param AssignmentFile $assignmentFile soubor zadání
     */
    public function downloadFile(AssignmentFile $assignmentFile): never
    {
        $file = DOCUMENT_FOLDER . '/' . $assignmentFile->studentId . '/' . $assignmentFile->assignmentId . '/' . $assignmentFile->location;
        header('Content-Type: ' . filetype($file));
        header('Content-Disposition: attachment; filename="' . $assignmentFile->filename . '"');
        header('Content-Length: ' . filesize($file));
        readfile($file);
        exit;
    }

    /**
     * Připraví soubor ve formátu ZIP obsahující vygenerovaná zadání a vypracování všech studentů.
     *
     * @param Assignment $assignment zadání
     */
    public function downloadWholeGroup(Assignment $assignment): never
    {
        $students = [];
        $files = $this->databaseManager->getAllAssignmentFiles($assignment->id);

        $zipFileName = tempnam('/tmp', 'ZIP');
        $zip = new ZipArchive();
        if ($zip->open($zipFileName, ZipArchive::CREATE) !== true) {
            die('Could not create ZIP file');
        }

        foreach ($files as $file) {
            if (!isset($students[$file->studentId])) {
                $students[$file->studentId] = $this->databaseManager->getStudentById($file->studentId);
            }

            $inFile = DOCUMENT_FOLDER . '/' . $file->studentId . '/' . $file->assignmentId . '/' . $file->location;
            $outFile = $students[$file->studentId]->studentNumber . '/' . $file->filename;
            $zip->addFile($inFile, $outFile);
        }

        $zip->close();

        header('Content-Type: application/zip');
        header('Content-Disposition: attachment; filename="zadani_' . $assignment->id . '.zip"');
        header('Content-Length: ' . filesize($zipFileName));
        readfile($zipFileName);
        @unlink($zipFileName);
        exit;
    }

    /**
     * Smaže vygenerované studentovo zadání
     *
     * @param int $assignmentId ID zadání
     * @param int $studentId ID studenta
     */
    public function purgeDocuments(int $assignmentId, int $studentId): void
    {
        $assignmentFiles = $this->databaseManager->getStudentAssignmentFiles($assignmentId, $studentId);

        foreach ($assignmentFiles as $assignmentFile) {
            @unlink(DOCUMENT_FOLDER . '/' . $studentId . '/' . $assignmentId . '/' . $assignmentFile->location);

            $this->databaseManager->removeAssignmentFile($assignmentFile->id);
        }
    }

    /**
     * Uloží nahraný soubor vypracování do složky studenta.
     *
     * @param int $assignmentId ID zadání
     * @param Student $student objekt studenta
     * @param array{name: string, tmp_name: string} $file pole obsahující informace o nahraném souboru
     * @return int|false ID nahraného souboru nebo false při neúspěchu
     */
    public function uploadFile(int $assignmentId, Student $student, array $file): int|false
    {
        $location = $student->studentNumber . '_odevzdani_' . date('YmdHis') . '_' . basename($file['name']);
        $fileName = DOCUMENT_FOLDER . '/' . $student->id . '/' . $assignmentId . '/' . $location;
        move_uploaded_file($file['tmp_name'], $fileName);
        return $this->databaseManager->addAssignmentFile($assignmentId, $student->id, basename($file['name']), FileType::UPLOAD, $location);
    }
}
