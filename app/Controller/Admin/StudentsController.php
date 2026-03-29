<?php

declare(strict_types=1);

namespace App\Controller\Admin;

use App\Model\AssignmentManager;
use App\Model\Database\Entities\Assignment;
use App\Model\Database\Entities\AssignmentProfile;
use App\Model\Database\Entities\ScheduledEvent;
use App\Model\Database\Entities\Student;
use App\Model\Database\Entities\Subject;
use App\Model\Database\Types\AssignmentState;
use App\Model\Database\Types\LogType;
use App\Model\Database\Types\Options;
use App\Model\Database\Types\FileType;
use App\Model\CheckerReportManager;
use App\Model\ChecksConfigManager;
use App\Model\StagExportManager;
use DateTime;

/**
 * Controller sloužící ke správě studentů a vypsaných zadání jedné rozvrhové akce.
 *
 * @author Michal Turek
 */
class StudentsController extends BaseAdminController
{
    protected function process(): void
    {
        if (!isset($_GET['event']) || !is_numeric($_GET['event'])) {
            $this->redirect('admin');
            return;
        }

        $currentYear = $this->getDatabase()->getOption(Options::YEAR);
        if (!$currentYear || !is_numeric($currentYear)) {
            $this->redirect('admin');
            return;
        }

        // pro každou akci v tomto Controlleru je potřeba mít k dispozici rozvrhovou akci a k dané akci musí mít uživatel přidělen přístup
        $event = $this->getDatabase()->getScheduledEventById((int) $_GET['event']);
        if (!$event || !in_array($this->loggedUser->id, $this->getDatabase()->getTeacherIdsByScheduledEvent($event->id))) {
            $this->redirect('admin');
            return;
        }

        $subject = $this->getDatabase()->getSubjectById($event->subjectId);

        $this->templateData['event'] = $event;
        $this->templateData['subject'] = $subject;

        $action = $_GET['action'] ?? 'default';
        switch ($action) {
            case 'default':
                $this->actionDefault($event);
                break;
            case 'add':
                $this->actionAdd($event, $subject);
                break;
            case 'edit':
                $this->actionEdit($event, $subject);
                break;
            case 'add-to-exam':
                $this->actionAddToExam($event, $subject);
                break;
            case 'add-assignment':
                $this->actionAddAssignment($event);
                break;
            case 'edit-assignment':
                $this->actionEditAssignment($event);
                break;
            case 'assign':
                $this->actionAssign($event);
                return;
            case 'deassign':
                $this->actionDeassign($event);
                return;
            case 'generate':
                $this->actionGenerate($event);
                return;
            case 'generate-all':
                $this->actionGenerateAll($event);
                return;
            case 'show':
                $this->actionShow($event);
                break;
            case 'download':
                $this->actionDownload($event);
                break;
            case 'download-all':
                $this->actionDownloadAll($event);
                break;
            case 'show-logs':
                $this->actionShowLogs($event);
                break;
            case 'upload-stag':
                $this->actionUploadStag($event, $subject);
                break;
            case 'upload-stag-exam':
                $this->actionUploadStagExam($event, $subject);
                break;
            case 'export-submitted-stag-csv':
                $this->actionExportSubmittedStagCsv($event);
                return;
            case 'checks-config':
                $this->actionChecksConfig($event);
                break;
            default:
                $this->error404();
                return;
        }
        $this->templateData['action'] = $action;
    }

    // AKCE
    /**
     * Zobrazí a zpracuje konfiguraci kontrol pro konkrétní zadání.
     * Konfigurace je navázána na konkrétní assignment, nikoliv na celý předmět.
     * Podle typu profilu zadání se následně v šabloně zobrazí buď textové,
     * nebo tabulkové kontroly.
     *
     * @param ScheduledEvent $event vypsaná akce
     * @return void
     * @author Adam Vaněček
     */
    private function actionChecksConfig(ScheduledEvent $event): void
    {
        if (!isset($_GET['assignment'])) {
            $this->error404();
            return;
        }
        $configManager = new ChecksConfigManager();
        $assignmentId = (int) $_GET['assignment'];
        $assignment = $this->getDatabase()->getAssignmentById($assignmentId);

        if (!$assignment || $assignment->scheduledEventId !== $event->id) {
            $this->error404();
            return;
        }

        $profile = $this->getDatabase()->getAssignmentProfileById($assignment->assignmentProfileId);
        if (!$profile) {
            $this->error404();
            return;
        }

        $showTextChecks = $profile->type === \App\Model\Database\Types\ProfileType::DOCUMENT;
        $showSheetChecks = $profile->type === \App\Model\Database\Types\ProfileType::TABLE_PROCESSOR;

        $textDefs = $configManager->getAllCheckDefinitions('text');
        $sheetDefs = $configManager->getAllCheckDefinitions('spreadsheet');

        $defaultTextMap = $configManager->buildDefaultMap($textDefs);
        $defaultSheetMap = $configManager->buildDefaultMap($sheetDefs);

        $dbCfg = $this->getDatabase()->getChecksConfigByAssignmentId($assignment->id) ?? [];

        $textMap = $configManager->sanitizeEnabledMap($dbCfg['text'] ?? null, $defaultTextMap);
        $sheetMap = $configManager->sanitizeEnabledMap($dbCfg['spreadsheet'] ?? null, $defaultSheetMap);

        $studentViewCfg = is_array($dbCfg['student_view'] ?? null) ? $dbCfg['student_view'] : [];

        $studentViewEnabled = (bool)($studentViewCfg['enabled'] ?? false);
        $studentViewMinPenalty = abs((int)($studentViewCfg['min_penalty'] ?? 100));

        if (isset($_POST['admin_checks_config_upload'])) {
            $this->processChecksConfigUploadForm($event, $assignment, $defaultTextMap, $defaultSheetMap);
            return;
        }

        if (isset($_POST['admin_checks_config_save'])) {
            $this->processChecksConfigSaveForm($event, $assignment, $defaultTextMap, $defaultSheetMap);
            return;
        }

        if (isset($_POST['admin_checks_config_reset'])) {
            $this->getDatabase()->saveChecksConfigForAssignment(
                $assignment->id,
                $defaultTextMap,
                $defaultSheetMap,
                false,
                -100
            );
            $this->getDatabase()->log(
                "Konfigurace kontrol byla obnovena na výchozí (zadání ID={$assignment->id}, akce ID={$event->id}).",
                LogType::SUBMIT,
                userId: $this->loggedUser->id
            );
            $this->alertMessage('success', 'Konfigurace kontrol byla obnovena na výchozí.');
            $this->redirect('admin/students', [
                'event' => $event->id,
                'action' => 'checks-config',
                'assignment' => $assignment->id,
            ]);
            return;
        }

        $textChecks = [];
        foreach ($textDefs as $d) {
            $code = $d['code'];
            $textChecks[] = [
                'code' => $code,
                'title' => $d['title'] ?? '',
                'enabled' => (bool)($textMap[$code] ?? false),
            ];
        }

        $sheetChecks = [];
        foreach ($sheetDefs as $d) {
            $code = $d['code'];
            $sheetChecks[] = [
                'code' => $code,
                'title' => $d['title'] ?? '',
                'enabled' => (bool)($sheetMap[$code] ?? false),
            ];
        }

        $this->templateData['textChecks'] = $textChecks;
        $this->templateData['sheetChecks'] = $sheetChecks;
        $this->templateData['assignment'] = $assignment;
        $this->templateData['profile'] = $profile;
        $this->templateData['showTextChecks'] = $showTextChecks;
        $this->templateData['showSheetChecks'] = $showSheetChecks;
        $this->templateData['event'] = $event;
        $this->templateData['studentViewEnabled'] = $studentViewEnabled;
        $this->templateData['studentViewMinPenalty'] = $studentViewMinPenalty;
    }
    
    /**
     * Zpracuje nahrání JSON konfigurace kontrol pro konkrétní zadání.
     *
     * @param ScheduledEvent $event vypsaná akce
     * @param Assignment $assignment zadání, pro které se konfigurace ukládá
     * @param array $defaultTextMap výchozí mapa textových kontrol
     * @param array $defaultSheetMap výchozí mapa tabulkových kontrol
     * @return void
     * @author Adam Vaněček
     */
    private function processChecksConfigUploadForm(
        ScheduledEvent $event,
        Assignment $assignment,
        array $defaultTextMap,
        array $defaultSheetMap
    ): void {
        if (!isset($_FILES['file']['tmp_name'], $_FILES['file']['error']) || $_FILES['file']['error'] !== 0) {
            $this->alertMessage('danger', 'Musíte nahrát JSON soubor.');
            return;
        }

        $raw = file_get_contents($_FILES['file']['tmp_name']);
        $data = json_decode((string)$raw, true);

        if (!is_array($data)) {
            $this->alertMessage('danger', 'Neplatný JSON.');
            return;
        }

        if (!array_key_exists('text', $data) || !array_key_exists('spreadsheet', $data)) {
            $this->alertMessage('danger', 'JSON musí obsahovat klíče "text" a "spreadsheet".');
            return;
        }
        
        $configManager = new ChecksConfigManager();
        $textRaw = $configManager->assertConfigSectionIsMap($data['text']);
        $sheetRaw = $configManager->assertConfigSectionIsMap($data['spreadsheet']);

        if ($textRaw === null || $sheetRaw === null) {
            $this->alertMessage('danger', 'JSON musí mít formát mapy: "text": { "T_...": true/false } a "spreadsheet": { "S_...": true/false }.');
            return;
        }

        $textMap = $configManager->sanitizeEnabledMap($textRaw, $defaultTextMap);
        $sheetMap = $configManager->sanitizeEnabledMap($sheetRaw, $defaultSheetMap);

        $studentViewRaw = is_array($data['student_view'] ?? null) ? $data['student_view'] : [];

        $studentViewEnabled = (bool)($studentViewRaw['enabled'] ?? false);

        $studentViewMinPenalty = -100;
        if (isset($studentViewRaw['min_penalty']) && is_numeric($studentViewRaw['min_penalty'])) {
            $studentViewMinPenalty = (int)$studentViewRaw['min_penalty'];
        }

        $this->getDatabase()->saveChecksConfigForAssignment(
            $assignment->id,
            $textMap,
            $sheetMap,
            $studentViewEnabled,
            $studentViewMinPenalty
        );

       $this->getDatabase()->log(
            "Konfigurace kontrol byla nahrána (zadání ID={$assignment->id}, akce ID={$event->id}).",
            LogType::SUBMIT,
            userId: $this->loggedUser->id
        );

        $this->alertMessage('success', 'Konfigurace kontrol byla nahrána.');
        $this->redirect('admin/students', [
            'event' => $event->id,
            'action' => 'checks-config',
            'assignment' => $assignment->id,
        ]);
    }

    /**
     * Zpracuje ruční uložení konfigurace kontrol pro konkrétní zadání.
     *
     * @param ScheduledEvent $event vypsaná akce
     * @param Assignment $assignment zadání, pro které se konfigurace ukládá
     * @param array $defaultTextMap výchozí mapa textových kontrol
     * @param array $defaultSheetMap výchozí mapa tabulkových kontrol
     * @return void
     * @author Adam Vaněček
     */
    private function processChecksConfigSaveForm(
        ScheduledEvent $event,
        Assignment $assignment,
        array $defaultTextMap,
        array $defaultSheetMap
    ): void {
        $textPost  = $_POST['text'] ?? [];
        $sheetPost = $_POST['spreadsheet'] ?? [];

        if (!is_array($textPost)) {
            $textPost = [];
        }
        if (!is_array($sheetPost)) {
            $sheetPost = [];
        }

        $textMap  = $defaultTextMap;
        $sheetMap = $defaultSheetMap;

        foreach ($textMap as $code => $_) {
            $textMap[$code] = isset($textPost[$code]) && (string)$textPost[$code] === '1';
        }

        foreach ($sheetMap as $code => $_) {
            $sheetMap[$code] = isset($sheetPost[$code]) && (string)$sheetPost[$code] === '1';
        }

        $studentViewEnabled = isset($_POST['student_view_enabled']) && (string)$_POST['student_view_enabled'] === '1';

        $studentViewMinPenalty = -100;
        if (isset($_POST['student_view_min_penalty']) && is_numeric($_POST['student_view_min_penalty'])) {
            $studentViewMinPenalty = (int)$_POST['student_view_min_penalty'];
        }

        $this->getDatabase()->saveChecksConfigForAssignment(
            $assignment->id,
            $textMap,
            $sheetMap,
            $studentViewEnabled,
            $studentViewMinPenalty
        );

        $this->getDatabase()->log(
            "Konfigurace kontrol byla uložena (zadání ID={$assignment->id}, akce ID={$event->id}).",
            LogType::SUBMIT,
            userId: $this->loggedUser->id
        );

        $this->alertMessage('success', 'Konfigurace kontrol byla uložena.');
        $this->redirect('admin/students', [
            'event' => $event->id,
            'action' => 'checks-config',
            'assignment' => $assignment->id,
        ]);
    }

    /**
     * Vygeneruje CSV export studentů s kompletně odevzdanými zadáními pro STAG.
     *
     * @param ScheduledEvent $event vypsaná akce
     * @return void
     * @author Adam Vaněček
     */
    private function actionExportSubmittedStagCsv(ScheduledEvent $event): void
    {
        $subject = $this->getDatabase()->getSubjectById($event->subjectId);
        if (!$subject) {
            $this->error404();
            return;
        }

        $students = $this->getDatabase()->getStudentsFullySubmittedByEvent($event->id);

        if (!$students) {
            $this->alertMessage('danger', 'Neexistuje žádný student, který má odevzdaná všechna zadání.');
            $this->redirect('admin/students', ['event' => $event->id]);
            return;
        }
        $stagExportManager = new StagExportManager();
        [$katedra, $zkratka] = $stagExportManager->splitSubjectShortcut($subject->shortcut);

        $rawSemester = $subject->semester;

        if (is_object($rawSemester) && property_exists($rawSemester, 'value')) {
            $rawSemester = $rawSemester->value;
        }

        $semestr = $stagExportManager->semesterToStag((string)$rawSemester);

        $rok = (string)$subject->year;

        $filename = "stag_export_splneno_event_{$event->id}_" . date('Y-m-d_H-i') . ".csv";
                

        header('Content-Type: text/csv; charset=utf-8');
        header('Content-Disposition: attachment; filename="' . $filename . '"');
        header('Pragma: no-cache');
        header('Expires: 0');

        $out = fopen('php://output', 'w');

        $header = [
            'katedra',
            'zkratka',
            'rok',
            'semestr',
            'os_cislo',
            'jmeno',
            'prijmeni',
            'titul',
            'nesplnene_prerekvizity',
            'zk_typ_hodnoceni',
            'zk_hodnoceni',
            'zk_body',
            'zk_datum',
            'zk_pokus',
            'zk_ucit_idno',
            'zk_jazyk',
            'zk_ucit_jmeno',
        ];
        fputcsv($out, $header, ';');

        foreach ($students as $s) {
            $state = $this->getDatabase()->getOverallStateForStudentOnEvent($event->id, (int)$s['id']);

            $zk_hodnoceni = '';
            if ($state === AssignmentState::ACCEPTED) $zk_hodnoceni = 'S';
            elseif ($state === AssignmentState::REJECTED) $zk_hodnoceni = 'N';
            
            $lastUpload = $this->getDatabase()->getLatestUploadTimeForStudentOnEvent($event->id, (int)$s['id']);
            $zk_datum = $lastUpload ? $lastUpload->format('d.m.Y') : '';

            $row = [
                $katedra,
                $zkratka,
                $rok,
                $semestr,
                (string)$s['student_number'], 
                (string)$s['name'],
                (string)$s['surname'],
                '', // titul 
                '', // nesplnene_prerekvizity
                '', // zk_typ_hodnoceni 
                $zk_hodnoceni, 
                '', // zk_body 
                $zk_datum, // zk_datum 
                '1', // zk_pokus
                '', // zk_ucit_idno
                '', // zk_jazyk
                '', // zk_ucit_jmeno
            ];

            fputcsv($out, $row, ';');
        }

        fclose($out);
        $this->getDatabase()->log(
            "Byl vygenerován export STAG CSV (akce ID={$event->id}, počet studentů=" . count($students) . ", soubor={$filename}).",
            LogType::SUBMIT,
            userId: $this->loggedUser->id
        );
        exit;
    }

    /**
     * Výchozí akce Controlleru pro výpis studentů a zadání na konkrétní rovrhové akci.
     *
     * @param ScheduledEvent $event rozvrhová akce
     */
    private function actionDefault(ScheduledEvent $event): void
    {
        $students = array_merge(
            $this->getDatabase()->getStudentsByScheduledEvent($event->id),
            $this->getDatabase()->getStudentsAssignedToExam($event->id),
        );
        $assignments = $this->getDatabase()->getAllAssignmentsByEvent($event->id);
        $studentWithAssignments = [];
        foreach ($students as $student) {
            $result = [
                'student' => $student,
                'assignments' => [],
            ];

            foreach ($assignments as $assignment) {
                $details = $this->getDatabase()->getStudentAssignmentDetails($assignment->id, $student->id);
                if ($details !== null) {
                    $result['assignments'][$assignment->id] = $details;
                }
            }

            $studentWithAssignments[] = $result;
        }

        $this->templateData['students'] = $studentWithAssignments;
        $this->templateData['assignments'] = $assignments;
    }

    /**
     * Akce pro přidání nového studenta.
     *
     * @param ScheduledEvent $event rozvrhová akce
     * @param Subject $subject předmět
     */
    private function actionAdd(ScheduledEvent $event, Subject $subject): void
    {
        if (isset($_POST['admin_students_add_form'])) {
            $this->processStudentsAddForm($event, $subject);
        }
    }

    /**
     * Akce pro úpravu existujícího studenta
     *
     * @param ScheduledEvent $event rozvrhová akce
     * @param Subject $subject předmět
     */
    private function actionEdit(ScheduledEvent $event, Subject $subject): void
    {
        if (!isset($_GET['id'])) {
            $this->error404();
            return;
        }

        $id = (int) $_GET['id'];
        $student = $this->getDatabase()->getStudentById($id);
        if (!$student || $student->scheduledEventId !== $event->id) {
            $this->error404();
            return;
        }

        if (isset($_POST['admin_students_edit_form'])) {
            $this->processStudentEditForm($student, $subject);
        } else {
            $this->templateData['post'] = [
                'studentNumber' => $student->studentNumber,
                'orion' => $student->orion,
                'name' => $student->name,
                'surname' => $student->surname,
            ];
        }
    }

    /**
     * Akce pro přidání studentů z jiných rozvrhových akcí do zápočtového termínu. Nelze využít pro normální rozvrhovou akci.
     *
     * @param ScheduledEvent $event rozvrhová akce
     * @param Subject $subject předmět
     */
    private function actionAddToExam(ScheduledEvent $event, Subject $subject): void
    {
        if (!$event->isExam) {
            $this->error404();
        }

        if (isset($_POST['admin_students_add_to_exam_form'])) {
            $this->processStudentsAddToExamForm($event);
        }

        $allEvents = $this->getDatabase()->getScheduledEventsBySubject($subject->id);
        $allStudents = [];
        foreach ($allEvents as $i => $subjectEvent) {
            if ($subjectEvent->isExam || $subjectEvent->id === $event->id) {
                unset($allEvents[$i]);
                continue;
            }

            $items = $this->getDatabase()->getStudentsByScheduledEvent($subjectEvent->id);
            if ($items) {
                $allStudents[$subjectEvent->id] = $items;
            } else {
                unset($allEvents[$i]);
            }
        }

        $this->templateData['allEvents'] = $allEvents;
        $this->templateData['allStudents'] = $allStudents;
        $this->templateData['assignedStudents'] = $this->getDatabase()->getStudentsAssignedToExamIds($event->id);
    }

    /**
     * Akce pro vytvoření nového zadání v dané rozvrhové akci.
     *
     * @param ScheduledEvent $event rozvrhová akce
     */
    private function actionAddAssignment(ScheduledEvent $event): void
    {
        $profiles = $this->getDatabase()->getAllAssignmentProfiles();
        $students = array_merge(
            $this->getDatabase()->getStudentsByScheduledEvent($event->id),
            $this->getDatabase()->getStudentsAssignedToExam($event->id),
        );

        if (isset($_POST['admin_students_assignment_add_form'])) {
            $this->processCreateAssignmentForm($event, $profiles, $students);
        }

        $this->templateData['profiles'] = $profiles;
        $this->templateData['students'] = $students;
    }

    /**
     * Akce pro úpravu zadání.
     *
     * @param ScheduledEvent $event rozvrhová akce
     */
    private function actionEditAssignment(ScheduledEvent $event): void
    {
        if (!isset($_GET['id'])) {
            $this->error404();
            return;
        }

        $id = (int) $_GET['id'];
        $assignment = $this->getDatabase()->getAssignmentById($id);
        if (!$assignment || $assignment->scheduledEventId !== $event->id) {
            $this->error404();
            return;
        }

        $profiles = $this->getDatabase()->getAllAssignmentProfiles();

        if (isset($_POST['admin_students_assignment_edit_form'])) {
            $this->processEditAssignmentForm($assignment, $profiles);
        } else {
            $this->templateData['post'] = [
                'profile' => $assignment->assignmentProfileId,
                'name' => $assignment->name,
                'dateFrom' => $assignment->dateFrom->format('Y-m-d\TH:i'),
                'dateTo' => $assignment->dateTo->format('Y-m-d\TH:i'),
            ];
        }

        $this->templateData['profiles'] = $profiles;
    }

    /**
     * Akce pro přiřazení studenta k zadání. Při přiřazení nedojde k vygenerování souborů zadání,
     * ale pouze k označení studenta pro pozdější generování.
     *
     * @param ScheduledEvent $event rozvrhová akce
     */
    private function actionAssign(ScheduledEvent $event): void
    {
        if (!isset($_GET['id'], $_GET['assignment'])) {
            $this->error404();
            return;
        }

        $id = (int) $_GET['id'];
        $assignmentId = (int) $_GET['assignment'];
        $assignment = $this->getDatabase()->getAssignmentById($assignmentId);
        $student = $this->getDatabase()->getStudentById($id);
        if (!$assignment || $assignment->scheduledEventId !== $event->id || !$student) {
            $this->error404();
            return;
        }

        $existing = $this->getDatabase()->getStudentAssignmentDetails($assignmentId, $id);
        if ($existing !== null) {
            $this->alertMessage('danger', 'Zadání je již přiřazeno');
            $this->redirect('admin/students', ['event' => $event->id]);
            return;
        }

        if ($this->getDatabase()->addStudentToAssignment($assignmentId, $id) === false) {
            $this->alertMessage('danger', 'Nepodařilo se přidat studenta do zadání');
        } else {
            $this->getDatabase()->log('Student ' . $student->name . ' ' . $student->surname . ' (ID ' . $student->id . ') byl přiřazen k zadání ' . $assignment->name . ' (ID' . $assignment->id . ')', LogType::ASSIGNMENT_STUDENT_ASSIGN, userId: $this->loggedUser->id);
            $this->alertMessage('success', 'Zadání bylo úspěšně přiřazeno');
        }
        $this->redirect('admin/students', ['event' => $event->id]);
    }

    /**
     * Akce pro odebrání studenta ze zadání. Nelze jej odebrat, pokud jḿají již zadání vygenerováno.
     *
     * @param ScheduledEvent $event rozvrhová akce
     */
    private function actionDeassign(ScheduledEvent $event): void
    {
        if (!isset($_GET['id'], $_GET['assignment'])) {
            $this->error404();
            return;
        }

        $id = (int) $_GET['id'];
        $assignmentId = (int) $_GET['assignment'];
        $assignment = $this->getDatabase()->getAssignmentById($assignmentId);
        $student = $this->getDatabase()->getStudentById($id);
        if (!$assignment || $assignment->scheduledEventId !== $event->id || !$student) {
            $this->error404();
            return;
        }

        $existing = $this->getDatabase()->getStudentAssignmentDetails($assignmentId, $id);
        if ($existing === null) {
            $this->alertMessage('danger', 'Zadání nebylo přiřazeno');
            $this->redirect('admin/students', ['event' => $event->id]);
            return;
        }
        if ($existing->generated) {
            $this->alertMessage('danger', 'Zadání již bylo vygenerováno');
            $this->redirect('admin/students', ['event' => $event->id]);
            return;
        }

        if (!$this->getDatabase()->removeStudentFromAssignment($assignmentId, $id)) {
            $this->alertMessage('danger', 'Nepodařilo se odebrat studenta ze zadání');
        } else {
            $this->getDatabase()->log('Student ' . $student->name . ' ' . $student->surname . ' (ID ' . $student->id . ') byl odebrán ze zadání ' . $assignment->name . ' (ID' . $assignment->id . ')', LogType::ASSIGNMENT_STUDENT_DEASSIGN, userId: $this->loggedUser->id);
            $this->alertMessage('success', 'Student byl úspěšně odebrán ze zadání');
        }
        $this->redirect('admin/students', ['event' => $event->id]);
    }

    /**
     * Akce pro vygenerování nebo přegenerování zadání jednomu studentovi.
     *
     * @param ScheduledEvent $event rozvrhová akce
     */
    private function actionGenerate(ScheduledEvent $event): void
    {
        if (!isset($_GET['id'], $_GET['assignment'])) {
            $this->error404();
            return;
        }

        $id = (int) $_GET['id'];
        $assignmentId = (int) $_GET['assignment'];
        $assignment = $this->getDatabase()->getAssignmentById($assignmentId);
        $student = $this->getDatabase()->getStudentById($id);
        if (!$assignment || $assignment->scheduledEventId !== $event->id || !$student) {
            $this->error404();
            return;
        }
        $profile = $this->getDatabase()->getAssignmentProfileById($assignment->assignmentProfileId);
        if (!$profile) {
            $this->error404();
            return;
        }

        $existing = $this->getDatabase()->getStudentAssignmentDetails($assignmentId, $id);
        if ($existing === null) {
            $this->alertMessage('danger', 'Zadání nebylo přiřazeno');
            $this->redirect('admin/students', ['event' => $event->id]);
            return;
        }

        $assignmentManager = new AssignmentManager($this->getDatabase());
        // Odebrání starého zadání
        $assignmentManager->purgeDocuments($assignmentId, $id);
        // Vygenerování nového
        $assignmentManager->generate($existing, $student, $profile);

        $this->getDatabase()->log('Studentovi ' . $student->name . ' ' . $student->surname . ' (ID ' . $student->id . ') byly vygenerovány soubory zadání ' . $assignment->name . ' (ID' . $assignment->id . ')', LogType::ASSIGNMENT_STUDENT_GENERATE, userId: $this->loggedUser->id);
        $this->alertMessage('success', 'Soubory zadání byly úspěšně vygenerovány');
        $this->redirect('admin/students', ['event' => $event->id]);
    }

    /**
     * Akce pro vygenerování zadání všem studentům, kteří zatím dané zadání vygenerováno nemají.
     *
     * @param ScheduledEvent $event rozvrhová akce
     */
    private function actionGenerateAll(ScheduledEvent $event): void
    {
        if (!isset($_GET['assignment'])) {
            $this->error404();
            return;
        }

        $assignmentId = (int) $_GET['assignment'];
        $assignment = $this->getDatabase()->getAssignmentById($assignmentId);
        if (!$assignment || $assignment->scheduledEventId !== $event->id) {
            $this->error404();
            return;
        }
        $profile = $this->getDatabase()->getAssignmentProfileById($assignment->assignmentProfileId);
        if (!$profile) {
            $this->error404();
            return;
        }

        $remainingAssignments = $this->getDatabase()->getStudentAssignmentsWithoutFiles($assignmentId);

        $assignmentManager = new AssignmentManager($this->getDatabase());
        $students = [];
        foreach ($remainingAssignments as $remainingAssignment) {
            $student = $this->getDatabase()->getStudentById($remainingAssignment->studentId);
            $assignmentManager->generate($remainingAssignment, $student, $profile);
            $students[] =  $student->name . ' ' . $student->surname . ' (ID ' . $student->id . ')';
        }

        $this->getDatabase()->log('Studentům ' . implode(', ', $students) . ' byly vygenerovány soubory zadání ' . $assignment->name . ' (ID' . $assignment->id . ')', LogType::ASSIGNMENT_STUDENT_GENERATE, userId: $this->loggedUser->id);
        $this->alertMessage('success', 'Soubory zadání byly úspěšně vygenerovány');
        $this->redirect('admin/students', ['event' => $event->id]);
    }
    
    /**
     * Zpracuje odeslání formuláře pro ignorování checker chyb.
     *
     * @param string|null $reportPath cesta k checker reportu
     * @param ScheduledEvent $event vypsaná akce
     * @param int $assignmentId ID zadání
     * @param int $id ID studenta
     * @return void
     * @author Adam Vaněček
     */
    private function handleCheckerIgnoreSubmit(
        CheckerReportManager $checkerManager,
        ?string $reportPath,
        ScheduledEvent $event,
        int $assignmentId,
        int $id
    ): void {
        if (!$reportPath || !is_file($reportPath)) return;
        if (!isset($_POST['checker_ignore_form'])) return;

        if ($checkerManager->applyCheckerIgnoresToReport($reportPath, $_POST)) {
            $this->alertMessage('success', 'Nastavení ignorovaných chyb bylo uloženo.');

            $url = $this->createLink('admin/students', [
                'event' => $event->id,
                'action' => 'show',
                'assignment' => $assignmentId,
                'id' => $id,
            ]) . '#auto-check';

            header('Location: ' . $url);
            exit;
        }
    }

    /**
     * Akce pro zobrazení detailu zadání konkrétního studenta, čili všech vygenerovaných i odevzdaných souborů.
     *
     * @param ScheduledEvent $event rozvrhová akce
     */
    private function actionShow(ScheduledEvent $event): void
    {
        if (!isset($_GET['id'], $_GET['assignment'])) {
            $this->error404();
            return;
        }

        $id = (int) $_GET['id'];
        $assignmentId = (int) $_GET['assignment'];
        $assignment = $this->getDatabase()->getAssignmentById($assignmentId);
        $student = $this->getDatabase()->getStudentById($id);
        if (!$assignment || $assignment->scheduledEventId !== $event->id || !$student) {
            $this->error404();
            return;
        }
        $profile = $this->getDatabase()->getAssignmentProfileById($assignment->assignmentProfileId);
        if (!$profile) {
            $this->error404();
            return;
        }

        $details = $this->getDatabase()->getStudentAssignmentDetails($assignmentId, $id);
        if ($details === null || !$details->generated) {
            $this->alertMessage('danger', 'Zadání ještě nebylo vygenerováno');
            $this->redirect('admin/students', ['event' => $event->id]);
            return;
        }

        if (isset($_POST['admin_students_rate_form'])) {
            $this->processStudentsRateForm($assignment, $student);
        }

        $this->templateData['student'] = $student;
        $this->templateData['assignment'] = $assignment;
        $this->templateData['details'] = $details;
        $this->templateData['files'] = $this->getDatabase()->getStudentAssignmentFiles($assignmentId, $id);
        
        // Author Adam Vaněček
        $checkerManager = new CheckerReportManager();
        $files = $this->getDatabase()->getStudentAssignmentFiles($assignmentId, $id);
        
        $this->templateData['files'] = $files;

        $checkerReport = null;

        $uploads = array_values(array_filter($files, fn($f) => $f->filetype === FileType::UPLOAD));
        usort($uploads, fn($a, $b) => $checkerManager->timeToTs($b->time) <=> $checkerManager->timeToTs($a->time));
        $latestUpload = $uploads[0] ?? null;
        $latestTime = $latestUpload ? $checkerManager->timeToTs($latestUpload->time) : 0;

        $baseDir = $checkerManager->getBaseDir($id, $assignmentId);
        $primaryPath = $baseDir . '/primary.json';

        $setPrimaryId = isset($_GET['setPrimary']) ? (int)$_GET['setPrimary'] : 0;
        if ($setPrimaryId) {
            $target = null;
            foreach ($uploads as $u) {
                if ((int)$u->id === $setPrimaryId) { $target = $u; break; }
            }

            if ($target) {
                $checkerManager->writePrimary($baseDir, $primaryPath, $target, $latestTime, true);

                $url = $this->createLink('admin/students', [
                    'event' => $event->id,
                    'action' => 'show',
                    'assignment' => $assignmentId,
                    'id' => $id,
                ]);

                header('Location: ' . $url);
                exit;
            }
        }

        $checkerManager->ensurePrimaryIsFresh($baseDir, $primaryPath, $latestUpload, $latestTime);

        $primaryUpload = $checkerManager->resolvePrimaryUpload($uploads, $primaryPath);
        $this->templateData['primaryUpload'] = $primaryUpload;

        $this->templateData['uploadPenalties'] = $checkerManager->buildUploadPenalties($baseDir, $uploads);

        if ($primaryUpload) {
            $reportPath = $checkerManager->findReportForUpload($baseDir, $primaryUpload->filename, $primaryUpload->time);

            $this->handleCheckerIgnoreSubmit($checkerManager,$reportPath, $event, $assignmentId, $id);

            $checkerReport = $checkerManager->loadCheckerReport($reportPath);
        }

        $suggestedComment = $checkerManager->buildSuggestedComment($checkerReport);
        $this->templateData['suggestedComment'] = $suggestedComment;
        $this->templateData['checkerReport'] = $checkerReport;
        // Author Adam Vaněček
    }

    /**
     * Akce pro stažení konkrétního souboru ze zadání jednoho studenta.
     *
     * @param ScheduledEvent $event rozvrhová akce
     */
    private function actionDownload(ScheduledEvent $event): void
    {
        if (!isset($_GET['id'], $_GET['assignment'], $_GET['file'])) {
            $this->error404();
            return;
        }

        $id = (int) $_GET['id'];
        $assignmentId = (int) $_GET['assignment'];
        $assignment = $this->getDatabase()->getAssignmentById($assignmentId);
        $student = $this->getDatabase()->getStudentById($id);
        if (!$assignment || $assignment->scheduledEventId !== $event->id || !$student) {
            $this->error404();
            return;
        }
        $file = $this->getDatabase()->getAssignmentFileById((int) $_GET['file']);
        if (!$file || $file->studentId !== $id || $file->assignmentId !== $assignmentId) {
            $this->error404();
            return;
        }

        $assignmentManager = new AssignmentManager($this->getDatabase());

        $assignmentManager->downloadFile($file);
    }

    /**
     * Akce pro stažení všech vygenerovaných i odevzdaných souborů v rámci jednoho zadání.
     *
     * @param ScheduledEvent $event rozvrhová akce
     */
    private function actionDownloadAll(ScheduledEvent $event): void
    {
        if (!isset($_GET['assignment'])) {
            $this->error404();
            return;
        }

        $assignmentId = (int) $_GET['assignment'];
        $assignment = $this->getDatabase()->getAssignmentById($assignmentId);
        if (!$assignment || $assignment->scheduledEventId !== $event->id) {
            $this->error404();
            return;
        }

        $assignmentManager = new AssignmentManager($this->getDatabase());

        $assignmentManager->downloadWholeGroup($assignment);
    }

    /**
     * Akce pro zobrazení záznamu aktivit konkrétního studenta.
     *
     * @param ScheduledEvent $event rozvrhová akce
     */
    private function actionShowLogs(ScheduledEvent $event): void
    {
        if (!isset($_GET['id'])) {
            $this->error404();
            return;
        }

        $id = (int) $_GET['id'];
        $student = $this->getDatabase()->getStudentById($id);
        if (!$student || $student->scheduledEventId !== $event->id) {
            $this->error404();
            return;
        }

        $page = 1;
        if (isset($_GET['pageNum']) && is_numeric($_GET['pageNum'])) {
            $page = (int) $_GET['pageNum'];
        }

        $this->templateData['student'] = $student;
        $this->templateData['limit'] = 20;
        $this->templateData['page'] = $page;
        $this->templateData['logCount'] = $this->getDatabase()->getLogCount($id);
        $this->templateData['logs'] = $this->getDatabase()->getLogs($page, 20, $id);
    }

    /**
     * Akce pro vytvoření studentů na rozvrhové akci podle souboru nahraného ze systému IS/STAG.
     *
     * @param ScheduledEvent $event rozvrhová akce
     * @param Subject $subject předmět
     */
    private function actionUploadStag(ScheduledEvent $event, Subject $subject): void
    {
        if (isset($_POST['admin_students_upload_from_stag'])) {
            $this->processStudentsUploadForm($event, $subject);
        }
    }

    /**
     * Akce pro přiřazení studentů k termínu podle souboru nahraného ze systému IS/STAG.
     *
     * @param ScheduledEvent $event rozvrhová akce
     * @param Subject $subject předmět
     */
    private function actionUploadStagExam(ScheduledEvent $event, ?Subject $subject)
    {
        if (!$event->isExam) {
            $this->error404();
        }

        if (isset($_POST['admin_students_upload_from_stag_exam'])) {
            $this->processStudentsUploadExamForm($event, $subject);
        }
    }

    // FORMULÁŘE

    /**
     * Metoda pro zpracování formuláře na vytvoření nového studenta.
     * Student musí mít v rámci akademického roku a semestru unikátní orion login i osobní číslo.
     *
     * @param ScheduledEvent $event rozvrhová akce
     * @param Subject $subject předmět
     */
    private function processStudentsAddForm(ScheduledEvent $event, Subject $subject): void
    {
        $post = [];

        $missing = false;

        if (isset($_POST['studentNumber'])) {
            $post['studentNumber'] = $_POST['studentNumber'];
        } else {
            $missing = true;
        }

        if (isset($_POST['orion'])) {
            $post['orion'] = $_POST['orion'];
        } else {
            $missing = true;
        }

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

        $this->templateData['post'] = $post;

        if ($missing) {
            $this->alertMessage('danger', 'Nejsou vyplněna všechna požadovaná pole');
            return;
        }

        if ($this->getDatabase()->checkIfOrionLoginIsUsed($post['orion'], $subject->year, $subject->semester)) {
            $this->alertMessage('danger', 'Tento orion login je již přiřazen jinému studentovi');
            return;
        }

        if ($this->getDatabase()->checkIfStudentNumberLoginIsUsed($post['studentNumber'], $subject->year, $subject->semester)) {
            $this->alertMessage('danger', 'Tento orion login je již přiřazen jinému studentovi');
            return;
        }

        $studentId = $this->getDatabase()->createStudent($event->id, $post['studentNumber'], $post['orion'], $post['name'], $post['surname']);
        if ($studentId === false) {
            $this->alertMessage('danger', 'Nepodařilo se přidat studenta');
            return;
        }

        $this->getDatabase()->log('Přidal studenta ' . $post['orion']  . ' (' . $post['name'] . ' ' . $post['surname'] . '; Rozvrhová akce ' . $event->id . '; ID ' . $studentId . '; Studentské číslo ' . $post['studentNumber'] . ')', LogType::STUDENT_ADD, userId: $this->loggedUser->id);
        $this->alertMessage('success', 'Student byl úspěšně přidán');
        $this->redirect('admin/students', ['event' => $event->id]);
    }

    /**
     * Metoda pro zpracování formuláře na nahrání CSV souboru ze systému IS/STAG.
     * Soubor se zpracovává jen do první chyby, následně je vypsán počet nově přidaných studentů.
     *
     * @param ScheduledEvent $event rozvrhová akce
     * @param Subject $subject předmět
     */
    private function processStudentsUploadForm(ScheduledEvent $event, Subject $subject): void
    {
        if (!isset($_FILES['file']['tmp_name'], $_FILES['file']['error']) || $_FILES['file']['error'] !== 0) {
            $this->alertMessage('danger', 'Musíte nahrát CSV soubor se studenty');
            return;
        }

        $data = [];

        if (($handle = fopen($_FILES['file']['tmp_name'], 'r')) !== FALSE) {
            $headers = fgetcsv($handle, 1000, ';');

            $requiredColumns = ['osCislo', 'jmeno', 'prijmeni', 'userName'];
            $indices = [];

            foreach ($headers as $index => $column) {
                if (in_array($column, $requiredColumns)) {
                    $indices[$column] = $index;
                }
            }

            // Ověření, že všechny požadované sloupce existují
            if (count($indices) !== count($requiredColumns)) {
                $this->alertMessage('danger', 'V CSV chybí některé požadované sloupce');
                return;
            }

            // Čtení dat
            while (($row = fgetcsv($handle, 1000, ";")) !== FALSE) {
                $rowData = [];
                foreach ($indices as $col => $index) {
                    $rowData[$col] = iconv('Windows-1250', 'UTF-8', $row[$index]);
                }
                $data[] = $rowData;
            }
            fclose($handle);
        }

        $finished = 0;
        foreach ($data as $row) {
            if ($this->getDatabase()->checkIfOrionLoginIsUsed($row['userName'], $subject->year, $subject->semester)) {
                continue;
            }

            if ($this->getDatabase()->checkIfStudentNumberLoginIsUsed($row['osCislo'], $subject->year, $subject->semester)) {
                continue;
            }

            $studentId = $this->getDatabase()->createStudent($event->id, $row['osCislo'], $row['userName'], $row['jmeno'], $row['prijmeni']);
            if ($studentId === false) {
                $this->alertMessage('danger', 'Nepodařilo se přidat studenta ' . $row['jmeno'] . ' ' . $row['prijmeni'] . '. Zpracováno ' . $finished . ' záznamů od začátku souboru.');
                $this->redirect('admin/students', ['event' => $event->id]);
                return;
            }
            $finished++;

            $this->getDatabase()->log('Přidal studenta ' . $row['userName']  . ' (' . $row['jmeno'] . ' ' . $row['prijmeni'] . '; Rozvrhová akce ' . $event->id . '; ID ' . $studentId . '; Studentské číslo ' . $row['osCislo'] . ')', LogType::STUDENT_ADD, userId: $this->loggedUser->id);
        }

        $this->alertMessage('success', 'Z nahraného souboru bylo importováno ' . $finished . ' nových studentů');
        $this->redirect('admin/students', ['event' => $event->id]);
    }

    /**
     * Metoda pro úpravu existujícího studenta.
     *
     * @param Student $student student
     * @param Subject $subject předmět
     */
    private function processStudentEditForm(Student $student, Subject $subject): void
    {
        $post = [];

        $missing = false;

        if (isset($_POST['studentNumber'])) {
            $post['studentNumber'] = $_POST['studentNumber'];
        } else {
            $missing = true;
        }

        if (isset($_POST['orion'])) {
            $post['orion'] = $_POST['orion'];
        } else {
            $missing = true;
        }

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

        $this->templateData['post'] = $post;

        if ($missing) {
            $this->alertMessage('danger', 'Nejsou vyplněna všechna požadovaná pole');
            return;
        }

        if ($student->orion !== $post['orion'] && $this->getDatabase()->checkIfOrionLoginIsUsed($post['orion'], $subject->year, $subject->semester)) {
            $this->alertMessage('danger', 'Tento orion login je již přiřazen jinému studentovi');
            return;
        }

        if ($student->studentNumber !== $post['studentNumber'] && $this->getDatabase()->checkIfStudentNumberLoginIsUsed($post['studentNumber'], $subject->year, $subject->semester)) {
            $this->alertMessage('danger', 'Tento orion login je již přiřazen jinému studentovi');
            return;
        }

        $result = $this->getDatabase()->updateStudent($student->id, $post['studentNumber'], $post['orion'], $post['name'], $post['surname']);
        if ($result === false) {
            $this->alertMessage('danger', 'Nepodařilo se upravit studenta');
            return;
        }

        $this->getDatabase()->log('Upraven studenta ' . $post['orion']  . ' (' . $post['name'] . ' ' . $post['surname'] . '; Rozvrhová akce ' . $student->scheduledEventId . '; ID ' . $student->id . '; Studentské číslo ' . $post['studentNumber'] . ')', LogType::STUDENT_EDIT, userId: $this->loggedUser->id);
        $this->alertMessage('success', 'Student byl úspěšně upraven');
        $this->redirect('admin/students', ['event' => $student->scheduledEventId]);
    }

    /**
     * Metoda pro zpracování formuláře na vytvoření nového zadání.
     * Během vytváření zadání je možné rovnou přiřadit studenty na rozvrhové akci k zadání.
     *
     * @param ScheduledEvent $event rozvrhová akce
     * @param AssignmentProfile[] $profiles profily zadání v systému
     * @param Student[] $students studenti na rozvrhové akci
     */
    private function processCreateAssignmentForm(ScheduledEvent $event, array $profiles, array $students): void
    {
        $post = [];

        $missing = false;

        if (isset($_POST['name'])) {
            $post['name'] = $_POST['name'];
        } else {
            $missing = true;
        }

        if (isset($_POST['profile'])) {
            $post['profile'] = $_POST['profile'];
        } else {
            $missing = true;
        }

        if (isset($_POST['dateFrom'])) {
            $post['dateFrom'] = $_POST['dateFrom'];
        } else {
            $missing = true;
        }

        if (isset($_POST['dateTo'])) {
            $post['dateTo'] = $_POST['dateTo'];
        } else {
            $missing = true;
        }

        if (isset($_POST['students'])) {
            $post['students'] = $_POST['students'];
        } else {
            $post['students'] = [];
        }

        $this->templateData['post'] = $post;

        if ($missing) {
            $this->alertMessage('danger', 'Nejsou vyplněna všechna požadovaná pole');
            return;
        }

        $selectedProfile = null;
        foreach ($profiles as $profile) {
            if ($profile->id == $post['profile']) {
                $selectedProfile = $profile;
            }
        }
        if ($selectedProfile === null) {
            $this->alertMessage('danger', 'Vybraný profil neexistuje');
            return;
        }

        $dateFrom = DateTime::createFromFormat('Y-m-d\TH:i', $post['dateFrom']);
        $dateTo = DateTime::createFromFormat('Y-m-d\TH:i', $post['dateTo']);
        if ($dateFrom === false) {
            $this->alertMessage('danger', 'Datum zadání nebyl poslán v požadovaném formátu');
            return;
        }

        if ($dateTo === false) {
            $this->alertMessage('danger', 'Datum odevzdání nebyl poslán v požadovaném formátu');
            return;
        }

        if ($dateFrom > $dateTo) {
            $this->alertMessage('danger', 'Datum zadání nemůže být později než datum odevzdání');
            return;
        }

        if (!is_array($post['students'])) {
            $this->alertMessage('danger', 'Seznam studentů nebyl přijat ve správném formátu');
            return;
        }

        $studentIds = array_map(fn (Student $student): int => $student->id, $students);
        foreach ($post['students'] as $student) {
            if (!in_array((int) $student, $studentIds)) {
                $this->alertMessage('danger', 'Byl vybrán neexistující student');
                return;
            }
        }

        $assignmentId = $this->getDatabase()->createAssignment($event->id, $selectedProfile->id, $dateFrom, $dateTo, $post['name']);
        if ($assignmentId === false) {
            $this->alertMessage('danger', 'Nepodařilo se přidat zadání');
            return;
        }

        foreach ($post['students'] as $student) {
            $this->getDatabase()->addStudentToAssignment($assignmentId, (int) $student);
        }

        $this->getDatabase()->log('Přidáno nové zadání ' . $post['name']  . ' (' . $selectedProfile->name . '; Rozvrhová akce ' . $event->id . '; ID ' . $assignmentId . '; Od ' . $dateFrom->format('Y-m-d H:i') . ' do ' . $dateTo->format('Y-m-d H:i') . ') pro ' . count($post['students']) . ' studentů', LogType::ASSIGNMENT_ADD, userId: $this->loggedUser->id);
        $this->alertMessage('success', 'Zadání bylo úspěšně vytvořeno');
        $this->redirect('admin/students', ['event' => $event->id]);
    }

    /**
     * Metoda pro zpracování formuláře na úpravu existujícího zadání.
     *
     * @param Assignment $assignment zadání
     * @param AssignmentProfile[] $profiles profily zadání v systému
     */
    private function processEditAssignmentForm(Assignment $assignment, array $profiles): void
    {
        $post = [];

        $missing = false;

        if (isset($_POST['name'])) {
            $post['name'] = $_POST['name'];
        } else {
            $missing = true;
        }

        if (isset($_POST['profile'])) {
            $post['profile'] = $_POST['profile'];
        } else {
            $missing = true;
        }

        if (isset($_POST['dateFrom'])) {
            $post['dateFrom'] = $_POST['dateFrom'];
        } else {
            $missing = true;
        }

        if (isset($_POST['dateTo'])) {
            $post['dateTo'] = $_POST['dateTo'];
        } else {
            $missing = true;
        }

        $this->templateData['post'] = $post;

        if ($missing) {
            $this->alertMessage('danger', 'Nejsou vyplněna všechna požadovaná pole');
            return;
        }

        $selectedProfile = null;
        foreach ($profiles as $profile) {
            if ($profile->id == $post['profile']) {
                $selectedProfile = $profile;
            }
        }
        if ($selectedProfile === null) {
            $this->alertMessage('danger', 'Vybraný profil neexistuje');
            return;
        }

        $dateFrom = DateTime::createFromFormat('Y-m-d\TH:i', $post['dateFrom']);
        $dateTo = DateTime::createFromFormat('Y-m-d\TH:i', $post['dateTo']);
        if ($dateFrom === false) {
            $this->alertMessage('danger', 'Datum zadání nebyl poslán v požadovaném formátu');
            return;
        }

        if ($dateTo === false) {
            $this->alertMessage('danger', 'Datum odevzdání nebyl poslán v požadovaném formátu');
            return;
        }

        if ($dateFrom > $dateTo) {
            $this->alertMessage('danger', 'Datum zadání nemůže být později než datum odevzdání');
            return;
        }

        $result = $this->getDatabase()->updateAssignment($assignment->id, $selectedProfile->id, $dateFrom, $dateTo, $post['name']);
        if ($result === false) {
            $this->alertMessage('danger', 'Nepodařilo se upravit zadání');
            return;
        }

        $this->getDatabase()->log('Upraveno zadání ' . $post['name']  . ' (' . $selectedProfile->name . '; Rozvrhová akce ' . $assignment->scheduledEventId . '; ID ' . $assignment->id . '; Od ' . $dateFrom->format('Y-m-d H:i') . ' do ' . $dateTo->format('Y-m-d H:i') . ')', LogType::STUDENT_EDIT, userId: $this->loggedUser->id);
        $this->alertMessage('success', 'Zadání bylo úspěšně upraveno');
        $this->redirect('admin/students', ['event' => $assignment->scheduledEventId]);
    }

    /**
     * Metoda pro zpracování formuláře na ohodnocení studentova vypracování.
     *
     * @param Assignment $assignment zadání
     * @param Student $student student
     */
    private function processStudentsRateForm(Assignment $assignment, Student $student): void
    {
        if (!isset($_POST['result']) || !is_numeric($_POST['result'])) {
            $this->alertMessage('danger', 'Hodnocení nebylo vybráno');
            return;
        }

        $result = AssignmentState::tryFrom((int) $_POST['result']);
        if ($result === null) {
            $this->alertMessage('danger', 'Hodnocení nebylo vybráno');
            return;
        }

        $comment = $_POST['comment'] ?? '';
        if (!is_string($comment)) {
            $this->alertMessage('danger', 'Komentář byl zaslán v neplatném formátu');
            return;
        }

        $dbResult = $this->getDatabase()->updateStudentRating($student->id, $assignment->id, $result, $comment);
        if ($dbResult === false) {
            $this->alertMessage('danger', 'Nepodařilo se uložit hodnocení');
            return;
        }

        $this->getDatabase()->log('Bylo změněno hodnocení studenta ' . $student->name . ' ' . $student->surname . '(ID ' . $student->id . ') u zadání ' . $assignment->name . ' (' . $assignment->id . ') na ' . $result->getText() . ' (Komentář: ' . $comment . ')', LogType::RATED, userId: $this->loggedUser->id);
        $this->alertMessage('success', 'Zadání bylo úspěšně upraveno');
        $this->redirect('admin/students', ['event' => $assignment->scheduledEventId, 'action' => 'show', 'assignment' => $assignment->id, 'id' => $student->id]);
    }

    /**
     * Metoda pro zpracování formuláře na přiřazení studentů jiných rozvrhových akcí k zápočtovému termínu.
     *
     * @param ScheduledEvent $event zápočtový termín
     */
    private function processStudentsAddToExamForm(ScheduledEvent $event): void
    {
        $students = $_POST['students'] ?? [];
        if (!is_array($students)) {
            $this->alertMessage('danger', 'Formulář nebyl odeslán ve správném formátu');
            return;
        }

        $studentIds = [];

        foreach ($students as $studentEvent) {
            if (!is_array($studentEvent)) {
                $this->alertMessage('danger', 'Formulář nebyl odeslán ve správném formátu');
                return;
            }

            $studentIds = array_merge($studentIds, array_map(fn (string $student): int => (int) $student, $studentEvent));
        }

        $assignedStudents = $this->getDatabase()->getStudentsAssignedToExamIds($event->id);

        foreach ($assignedStudents as $student) {
            if (($key = array_search($student, $studentIds)) !== false) {
                unset($studentIds[$key]);
            } else {
                $this->getDatabase()->removeStudentFromExam($event->id, $student);
            }
        }

        foreach ($studentIds as $studentId) {
            $this->getDatabase()->addStudentToExam($event->id, $studentId);
        }

        $this->getDatabase()->log('Byl změněn seznam studentů na termínu ' . $event->examDate?->format('j. n. Y') . ' ' . $event->timeFrom . ' - ' . $event->timeTo . ' (ID ' . $event->id . ')', LogType::EXAM_STUDENTS, userId: $this->loggedUser->id);
        $this->alertMessage('success', 'Zadání bylo úspěšně upraveno');
        $this->redirect('admin/students', ['event' => $event->id]);
    }

    /**
     * Metoda pro zpracování formuláře na nahrání CSV souboru ze systému IS/STAG.
     * Soubor se zpracovává jen do první chyby, následně je vypsán počet nově přidaných studentů.
     *
     * @param ScheduledEvent $event rozvrhová akce
     * @param Subject $subject předmět
     */
    private function processStudentsUploadExamForm(ScheduledEvent $event, Subject $subject): void
    {
        if (!isset($_FILES['file']['tmp_name'], $_FILES['file']['error']) || $_FILES['file']['error'] !== 0) {
            $this->alertMessage('danger', 'Musíte nahrát CSV soubor se studenty');
            return;
        }

        $data = [];

        if (($handle = fopen($_FILES['file']['tmp_name'], 'r')) !== FALSE) {
            $headers = fgetcsv($handle, 1000, ';');

            $requiredColumns = ['os_cislo'];
            $indices = [];

            foreach ($headers as $index => $column) {
                if (in_array($column, $requiredColumns)) {
                    $indices[$column] = $index;
                }
            }

            // Ověření, že všechny požadované sloupce existují
            if (count($indices) !== count($requiredColumns)) {
                $this->alertMessage('danger', 'V CSV chybí některé požadované sloupce');
                return;
            }

            // Čtení dat
            while (($row = fgetcsv($handle, 1000, ";")) !== FALSE) {
                $rowData = [];
                foreach ($indices as $col => $index) {
                    $rowData[$col] = iconv('Windows-1250', 'UTF-8', $row[$index]);
                }
                $data[] = $rowData;
            }
            fclose($handle);
        }

        $assignedStudents = $this->getDatabase()->getStudentsAssignedToExamIds($event->id);

        $finished = 0;
        foreach ($data as $row) {
            $student = $this->getDatabase()->getStudentByStudentNumber($row['os_cislo'], $subject->year, $subject->semester);

            if (!$student) {
                $this->alertMessage('danger', 'Nepodařilo se přidat studenta ' . $row['os_cislo'] . ' k tomuto termínu, jelikož v systému neexistuje. Zpracováno ' . $finished . ' záznamů od začátku souboru.');
                if ($finished > 0) {
                    $this->getDatabase()->log('Byl změněn seznam studentů na termínu ' . $event->examDate?->format('j. n. Y') . ' ' . $event->timeFrom . ' - ' . $event->timeTo . ' (ID ' . $event->id . ')', LogType::EXAM_STUDENTS, userId: $this->loggedUser->id);
                }
                $this->redirect('admin/students', ['event' => $event->id]);
                return;
            }

            if (in_array($student->id, $assignedStudents)) {
                continue;
            }


            $result = $this->getDatabase()->addStudentToExam($event->id, $student->id);
            if ($result === false) {
                $this->alertMessage('danger', 'Nepodařilo se přidat studenta ' . $row['os_cislo'] . ' k tomuto termínu. Zpracováno ' . $finished . ' záznamů od začátku souboru.');
                if ($finished > 0) {
                    $this->getDatabase()->log('Byl změněn seznam studentů na termínu ' . $event->examDate?->format('j. n. Y') . ' ' . $event->timeFrom . ' - ' . $event->timeTo . ' (ID ' . $event->id . ')', LogType::EXAM_STUDENTS, userId: $this->loggedUser->id);
                }
                $this->redirect('admin/students', ['event' => $event->id]);
                return;
            }
            $finished++;
        }

        if ($finished > 0) {
            $this->getDatabase()->log('Byl změněn seznam studentů na termínu ' . $event->examDate?->format('j. n. Y') . ' ' . $event->timeFrom . ' - ' . $event->timeTo . ' (ID ' . $event->id . ')', LogType::EXAM_STUDENTS, userId: $this->loggedUser->id);
        }

        $this->alertMessage('success', 'Z nahraného souboru bylo k termínu přiřazeno ' . $finished . ' nových studentů');
        $this->redirect('admin/students', ['event' => $event->id]);
    }
}
