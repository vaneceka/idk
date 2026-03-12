<?php

declare(strict_types=1);

namespace App\Model\Database;

use App\Model\Database\Entities\Assignment;
use App\Model\Database\Entities\AssignmentFile;
use App\Model\Database\Entities\AssignmentProfile;
use App\Model\Database\Entities\AssignmentStudent;
use App\Model\Database\Entities\FullAssignmentStudent;
use App\Model\Database\Entities\Log;
use App\Model\Database\Entities\ScheduledEvent;
use App\Model\Database\Entities\Student;
use App\Model\Database\Entities\Subject;
use App\Model\Database\Entities\User;
use App\Model\Database\Types\AssignmentState;
use App\Model\Database\Types\FileType;
use App\Model\Database\Types\LogType;
use App\Model\Database\Types\ProfileType;
use App\Model\Database\Types\Semester;
use DateTime;
use PDO;
use PDOException;
use PhpOffice\PhpSpreadsheet\Shared\Date;

/**
 * Třída slouží pro připojení a práci s databází.
 *
 * @author Michal Turek
 */
class DatabaseManager
{
    private readonly PDO $pdo;
    private const string PASSWORD_ALGORITHM = PASSWORD_BCRYPT;

    public function __construct()
    {
        $this->pdo = new PDO('mysql:host=' . DB_HOST . ';dbname=' . DB_NAME, DB_USER, DB_PASSWORD);
        $this->pdo->exec("set names utf8");
        $this->pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    }

    /**
     * Získá administrátora nebo vyučujícího podle id.
     *
     * @param int $id ID administrátora/vyučujícího
     * @return User|null objekt uživatele nebo null při neúspěchu
     */
    public function getAdminUserById(int $id): ?User
    {
        $stmt = $this->pdo->prepare("SELECT id, username, name, surname, admin FROM users WHERE id = :id");
        $stmt->bindValue(':id', $id);

        try {
            $stmt->execute();
        } catch (PDOException) {
            return null;
        }

        $result = $stmt->fetch(PDO::FETCH_ASSOC);
        if (!$result) {
            return null;
        }

        return new User(
            (int)$result['id'],
            $result['username'],
            $result['name'],
            $result['surname'],
            ((int)$result['admin']) === 1,
        );
    }

    /**
     * Získá administrátora nebo vyučujícího podle uživatelského jména a provede jeho autentizaci podle hesla.
     *
     * @param string $username uživatelské jméno
     * @param string $password heslo
     * @return User|null objekt uživatele, pokud byl nalezen a zadal správné heslo, jinak null
     */
    public function getAdminUserByNameAndTestAuthentication(string $username, #[\SensitiveParameter] string $password): ?User
    {
        $stmt = $this->pdo->prepare("SELECT id, username, name, surname, password, admin FROM users WHERE username = :username");
        $stmt->bindValue(':username', $username);

        try {
            $stmt->execute();
        } catch (PDOException) {
            return null;
        }

        $result = $stmt->fetch(PDO::FETCH_ASSOC);
        if (!$result) {
            return null;
        }

        if (!password_verify($password, $result['password'])) {
            return null;
        }

        if (password_needs_rehash($result['password'], self::PASSWORD_ALGORITHM)) {
            $stmt = $this->pdo->prepare("UPDATE users SET password = :password WHERE id = :id");
            $stmt->bindValue(':id', $result['id']);
            $stmt->bindValue(':password', password_hash($password, self::PASSWORD_ALGORITHM));
            $stmt->execute();
        }

        return new User(
            (int)$result['id'],
            $result['username'],
            $result['name'],
            $result['surname'],
            ((int)$result['admin']) === 1,
        );
    }

    /**
     * Zkontroluje, jestli v databázi existuje uživatel s uživatelským jménem.
     *
     * @param string $username uživatelské jméno
     * @return bool true, pokud uživatel existuje, jinak false
     */
    public function checkIfAdminUsernameExists(string $username): bool
    {
        $stmt = $this->pdo->prepare('SELECT COUNT(*) FROM users WHERE username = :username');
        $stmt->bindParam('username', $username);
        $stmt->execute();

        return (bool)$stmt->fetchColumn();
    }

    /**
     * Vytvoří nového administrátora nebo vyučujícího.
     *
     * @param string $username uživatelské jméno
     * @param string $name jméno
     * @param string $surname příjmení
     * @param string $password heslo
     * @param bool $isAdmin true, pokud se jedná o administrátora
     * @return int|false ID uživatele nebo false při neúspěchu
     */
    public function createAdminUser(
        string $username,
        string $name,
        string $surname,
        #[\SensitiveParameter]
        string $password,
        bool   $isAdmin,
    ): int|false
    {
        $hash = password_hash($password, self::PASSWORD_ALGORITHM);

        $stmt = $this->pdo->prepare('INSERT INTO users(username, name, surname, password, admin) VALUES (:username, :name, :surname, :password, :admin)');
        $stmt->bindValue(':username', $username);
        $stmt->bindValue(':name', $name);
        $stmt->bindValue(':surname', $surname);
        $stmt->bindValue(':password', $hash);
        $stmt->bindValue(':admin', $isAdmin ? 1 : 0, PDO::PARAM_INT);

        try {
            $stmt->execute();
        } catch (PDOException) {
            return false;
        }

        return (int)$this->pdo->lastInsertId();
    }

    /**
     * Upraví administrátora nebo vyučujícího.
     *
     * @param int $id ID uživatele
     * @param string $username nové uživatelské jméno
     * @param string $name nové jméno
     * @param string $surname nové příjmení
     * @param bool $isAdmin true, pokud se jedná o administrátora
     * @return bool true, pokud se úprava podařila, jinak false
     */
    public function updateAdminUser(
        int    $id,
        string $username,
        string $name,
        string $surname,
        bool   $isAdmin,
    ): bool
    {
        $stmt = $this->pdo->prepare('UPDATE users SET username = :username, name = :name, surname = :surname, admin = :admin WHERE id = :id');
        $stmt->bindValue(':id', $id);
        $stmt->bindValue(':username', $username);
        $stmt->bindValue(':name', $name);
        $stmt->bindValue(':surname', $surname);
        $stmt->bindValue(':admin', $isAdmin ? 1 : 0, PDO::PARAM_INT);

        try {
            $stmt->execute();
        } catch (PDOException) {
            return false;
        }

        return true;
    }

    /**
     * Odstraní administrátora nebo vyučujícího.
     *
     * @param int $id ID uživatele
     * @return bool true, pokud se operace podařila, jinak false
     */
    public function removeAdminUser(int $id): bool
    {
        $this->pdo->beginTransaction();
        $stmt = $this->pdo->prepare('DELETE FROM teachers WHERE user_id = :id');
        $stmt->bindValue(':id', $id);

        try {
            $stmt->execute();
        } catch (PDOException) {
            $this->pdo->rollBack();
            return false;
        }

        $stmt = $this->pdo->prepare('UPDATE logs SET user_id = NULL WHERE user_id = :id');
        $stmt->bindValue(':id', $id);

        try {
            $stmt->execute();
        } catch (PDOException) {
            $this->pdo->rollBack();
            return false;
        }

        $stmt = $this->pdo->prepare('DELETE FROM users WHERE id = :id');
        $stmt->bindValue(':id', $id);

        try {
            $stmt->execute();
            $this->pdo->commit();
        } catch (PDOException) {
            $this->pdo->rollBack();
            return false;
        }

        return true;
    }

    /**
     * Získá všechny administrátory a vyučující.
     *
     * @return User[] pole uživatelů
     */
    public function getAllAdminUsers(): array
    {
        $stmt = $this->pdo->prepare('SELECT id, username, name, surname, admin FROM users');
        $stmt->execute();
        $results = $stmt->fetchAll(PDO::FETCH_ASSOC);

        if (!$results) {
            return [];
        }

        return array_map(fn(array $result): User => new User(
            (int)$result['id'],
            $result['username'],
            $result['name'],
            $result['surname'],
            ((int)$result['admin']) === 1,
        ), $results);
    }

    /**
     * Získá všechny předměty pro zadaný akademický rok a semestr.
     *
     * @param int $year akademický rok
     * @param Semester $semester semestr
     * @return Subject[] pole předmětů
     */
    public function getSubjectsByYearAndSemester(int $year, Semester $semester): array
    {
        $stmt = $this->pdo->prepare('SELECT id, shortcut, name, year, semester FROM subjects WHERE year = :year AND semester = :semester');
        $stmt->bindValue(':year', $year);
        $stmt->bindValue(':semester', $semester->value);
        $stmt->execute();
        $results = $stmt->fetchAll(PDO::FETCH_ASSOC);

        if (!$results) {
            return [];
        }

        return array_map(fn(array $result): Subject => new Subject(
            (int)$result['id'],
            $result['shortcut'],
            $result['name'],
            (int)$result['year'],
            Semester::from($result['semester']),
        ), $results);
    }

    /**
     * Vytvoří nový předmět.
     *
     * @param string $shortcut zkratka předmětu (včetně názvu katedry).
     * @param string $name název předmětu
     * @param int $year akademický rok
     * @param Semester $semester semestr
     * @return int|false ID předmětu nebo false při neúspěchu
     */
    public function createSubject(
        string   $shortcut,
        string   $name,
        int      $year,
        Semester $semester,
    ): int|false
    {
        $stmt = $this->pdo->prepare('INSERT INTO subjects(shortcut, name, year, semester) VALUES (:shortcut, :name, :year, :semester)');
        $stmt->bindValue(':shortcut', $shortcut);
        $stmt->bindValue(':name', $name);
        $stmt->bindValue(':year', $year, PDO::PARAM_INT);
        $stmt->bindValue(':semester', $semester->value);

        try {
            $stmt->execute();
        } catch (PDOException) {
            return false;
        }

        return (int)$this->pdo->lastInsertId();
    }

    /**
     * Vrátí předmět podle id.
     *
     * @param int $id ID předmětu
     * @return Subject|null objekt předmětu nebo null, pokud neexistuje
     */
    public function getSubjectById(int $id): ?Subject
    {
        $stmt = $this->pdo->prepare('SELECT shortcut, name, year, semester FROM subjects WHERE id = :id');
        $stmt->bindValue(':id', $id);
        $stmt->execute();
        $result = $stmt->fetch(PDO::FETCH_ASSOC);

        if (!$result) {
            return null;
        }

        return new Subject(
            $id,
            $result['shortcut'],
            $result['name'],
            (int)$result['year'],
            Semester::from($result['semester']),
        );
    }

    /**
     * Vrátí rozvrhovou akci podle id.
     *
     * @param int $id ID rozvrhové akce
     * @return ScheduledEvent|null objekt rozvrhové akce nebo null, pokud neexistuje
     */
    public function getScheduledEventById(int $id): ?ScheduledEvent
    {
        $stmt = $this->pdo->prepare('SELECT subject_id, day, time_from, time_to, exam, exam_date FROM scheduled_events WHERE id = :id');
        $stmt->bindValue(':id', $id);
        $stmt->execute();
        $result = $stmt->fetch(PDO::FETCH_ASSOC);

        if (!$result) {
            return null;
        }

        return new ScheduledEvent(
            $id,
            (int)$result['subject_id'],
            (int)$result['day'],
            $result['time_from'],
            $result['time_to'],
            ((int) $result['exam']) === 1,
            $result['exam_date'] ? new DateTime($result['exam_date']) : null,
        );
    }

    /**
     * Upraví předmět.
     *
     * @param int $id ID předmětu
     * @param string $shortcut nová zkratka
     * @param string $name nový název
     * @return bool true, pokud se operace povedla, jinak false
     */
    public function updateSubject(
        int    $id,
        string $shortcut,
        string $name,
    ): bool
    {
        $stmt = $this->pdo->prepare('UPDATE subjects SET shortcut = :shortcut, name = :name WHERE id = :id');
        $stmt->bindValue(':id', $id);
        $stmt->bindValue(':shortcut', $shortcut);
        $stmt->bindValue(':name', $name);

        try {
            $stmt->execute();
        } catch (PDOException) {
            return false;
        }

        return true;
    }

    /**
     * Vrátí všechny rozvrhové akce daného předmětu.
     *
     * @param int $subject ID předmětu
     * @return ScheduledEvent[] pole rozvrhových akcí
     */
    public function getScheduledEventsBySubject(int $subject): array
    {
        $stmt = $this->pdo->prepare('SELECT id, subject_id, day, time_from, time_to, exam, exam_date FROM scheduled_events WHERE subject_id = :subject ORDER BY day ASC, time_from ASC');
        $stmt->bindValue(':subject', $subject);
        $stmt->execute();
        $results = $stmt->fetchAll(PDO::FETCH_ASSOC);

        if (!$results) {
            return [];
        }

        return array_map(fn(array $result): ScheduledEvent => new ScheduledEvent(
            (int)$result['id'],
            (int)$result['subject_id'],
            (int)$result['day'],
            $result['time_from'],
            $result['time_to'],
            ((int) $result['exam']) === 1,
            $result['exam_date'] ? new DateTime($result['exam_date']) : null,
        ), $results);
    }

    /**
     * Vytvoří novou rozvrhovou akci.
     *
     * @param int $subjectId ID předmětu
     * @param int $day den rozvrhové akce, v rozsahu od 1 do 7 (pondělí až neděle)
     * @param string $timeFrom čas začátku rozvrhové akce
     * @param string $timeTo čas konce rozvrhové akce
     * @param DateTime|null $examDate datum konání, pokud se jedná o jednorázovou rozvrhovou akci (termín), jinak null
     * @return int|false ID rozvrhové akce nebo false při neúspěchu
     */
    public function createScheduledEvent(
        int    $subjectId,
        int    $day,
        string $timeFrom,
        string $timeTo,
        ?DateTime $examDate,
    ): int|false
    {
        if ($day < 1 || $day > 7 || !preg_match("/^(?:2[0-3]|[01][0-9]):[0-5][0-9]$/", $timeFrom) || !preg_match("/^(?:2[0-3]|[01][0-9]):[0-5][0-9]$/", $timeTo)) {
            return false;
        }

        $stmt = $this->pdo->prepare('INSERT INTO scheduled_events(subject_id, day, time_from, time_to, exam, exam_date) VALUES (:subject_id, :day, :time_from, :time_to, :exam, :exam_date)');
        $stmt->bindValue(':subject_id', $subjectId, PDO::PARAM_INT);
        $stmt->bindValue(':day', $day, PDO::PARAM_INT);
        $stmt->bindValue(':time_from', $timeFrom);
        $stmt->bindValue(':time_to', $timeTo);
        $stmt->bindValue(':exam', $examDate !== null ? 1 : 0, PDO::PARAM_INT);
        $stmt->bindValue(':exam_date', $examDate?->format('Y-m-d'));

        try {
            $stmt->execute();
        } catch (PDOException) {
            return false;
        }

        return (int)$this->pdo->lastInsertId();
    }

    /**
     * Upraví rozvrhovou akci.
     *
     * @param int $eventId ID rozvrhové akce
     * @param int $day den rozvrhové akce, v rozsahu od 1 do 7 (pondělí až neděle)
     * @param string $timeFrom čas začátku rozvrhové akce
     * @param string $timeTo čas konce rozvrhové akce
     * @param DateTime|null $examDate datum konání, pokud se jedná o jednorázovou rozvrhovou akci (termín), jinak null
     * @return bool true, pokud se operace podařila, jinak false
     */
    public function updateScheduledEvent(
        int    $eventId,
        int    $day,
        string $timeFrom,
        string $timeTo,
        ?DateTime $examDate,
    ): bool
    {
        if ($day < 1 || $day > 7 || !preg_match("/^(?:2[0-3]|[01][0-9]):[0-5][0-9]$/", $timeFrom) || !preg_match("/^(?:2[0-3]|[01][0-9]):[0-5][0-9]$/", $timeTo)) {
            return false;
        }

        $stmt = $this->pdo->prepare('UPDATE scheduled_events SET day = :day, time_from = :time_from, time_to = :time_to, exam = :exam, exam_date = :exam_date WHERE id = :id');
        $stmt->bindValue(':id', $eventId, PDO::PARAM_INT);
        $stmt->bindValue(':day', $day, PDO::PARAM_INT);
        $stmt->bindValue(':time_from', $timeFrom);
        $stmt->bindValue(':time_to', $timeTo);
        $stmt->bindValue(':exam', $examDate !== null ? 1 : 0, PDO::PARAM_INT);
        $stmt->bindValue(':exam_date', $examDate?->format('Y-m-d'));

        try {
            $stmt->execute();
        } catch (PDOException) {
            return false;
        }

        return true;
    }

    /**
     * Změní přiřazení vyučujících k rozvrhové akci.
     *
     * @param int $eventId ID rozvrhové akce
     * @param int[] $teachers pole ID vyučujících
     */
    public function updateTeachers(int $eventId, array $teachers): bool
    {
        $stmt = $this->pdo->prepare('DELETE FROM teachers WHERE scheduled_event_id = :scheduled_event_id');
        $stmt->bindValue(':scheduled_event_id', $eventId);
        $stmt->execute();


        foreach ($teachers as $teacher) {
            $stmt = $this->pdo->prepare('INSERT INTO teachers(user_id, scheduled_event_id) VALUES (:user_id, :scheduled_event_id)');
            $stmt->bindValue(':user_id', $teacher);
            $stmt->bindValue(':scheduled_event_id', $eventId);
            $stmt->execute();
        }

        return true;
    }

    /**
     * Získá ID přiřazených vyučujících k rozvrhové akci.
     *
     * @param int $eventId ID rozvrhové akce
     * @return int[] pole s ID přiřazených vyučujících
     */
    public function getTeacherIdsByScheduledEvent(int $eventId): array
    {
        $stmt = $this->pdo->prepare('SELECT user_id FROM teachers WHERE scheduled_event_id = :scheduled_event_id');
        $stmt->bindValue(':scheduled_event_id', $eventId);
        $stmt->execute();
        $results = $stmt->fetchAll(PDO::FETCH_ASSOC);
        if (!$results) {
            return [];
        }

        return array_map(fn(array $result): int => $result['user_id'], $results);
    }

    /**
     * Získá přiřazené vyučující k rozvrhové akci.
     *
     * @param int $eventId ID rozvrhové akce
     * @return User[] pole s objekty přiřazených vyučujících
     */
    public function getTeachersByScheduledEvent(int $eventId): array
    {
        $stmt = $this->pdo->prepare('SELECT users.id, users.username, users.name, users.surname, users.admin FROM teachers JOIN users ON users.id=teachers.user_id WHERE teachers.scheduled_event_id = :scheduled_event_id');
        $stmt->bindValue(':scheduled_event_id', $eventId);
        $stmt->execute();
        $results = $stmt->fetchAll(PDO::FETCH_ASSOC);
        if (!$results) {
            return [];
        }

        return array_map(fn(array $result): User => new User(
            (int)$result['id'],
            $result['username'],
            $result['name'],
            $result['surname'],
            ((int)$result['admin']) === 1,
        ), $results);
    }

    /**
     * Vytvoří nový profil zadání.
     *
     * @param string $name název profilu
     * @param ProfileType $type typ profilu
     * @param array $options pole obsahující nastavení generátoru podle typu zadání
     * @return int|false ID profilu nebo false při neúspěchu
     */
    public function createAssignmentProfile(
        string      $name,
        ProfileType $type,
        array       $options,
    ): int|false
    {
        $stmt = $this->pdo->prepare('INSERT INTO assignment_profile(name, type, options) VALUES (:name, :type, :options)');
        $stmt->bindValue(':name', $name);
        $stmt->bindValue(':type', $type->value);
        $stmt->bindValue(':options', json_encode($options));

        try {
            $stmt->execute();
        } catch (PDOException) {
            return false;
        }

        return (int)$this->pdo->lastInsertId();
    }

    /**
     * Upraví profil zadání.
     *
     * @param int $id ID profilu zadání
     * @param string $name název profilu
     * @param ProfileType $type typ profilu
     * @param array $options pole obsahující nastavení generátoru podle typu zadání
     * @return bool true, pokud se operace podařila, jinak false
     */
    public function updateAssignmentProfile(
        int         $id,
        string      $name,
        ProfileType $type,
        array       $options,
    ): bool
    {
        $stmt = $this->pdo->prepare('UPDATE assignment_profile SET name = :name, type = :type, options = :options WHERE id = :id');
        $stmt->bindValue(':id', $id);
        $stmt->bindValue(':name', $name);
        $stmt->bindValue(':type', $type->value);
        $stmt->bindValue(':options', json_encode($options));

        try {
            $stmt->execute();
        } catch (PDOException) {
            return false;
        }

        return true;
    }

    /**
     * Smaže profil zadání.
     *
     * @param int $id ID profilu zadání
     * @return bool true, pokud se operace podařila, jinak false
     */
    public function removeAssignmentProfile(int $id): bool
    {
        $stmt = $this->pdo->prepare('DELETE FROM assignment_profile WHERE id = :id');
        $stmt->bindValue(':id', $id);

        try {
            $stmt->execute();
        } catch (PDOException) {
            return false;
        }

        return true;
    }

    /**
     * Získá všechny profily zadání.
     *
     * @return AssignmentProfile[] pole profilů
     */
    public function getAllAssignmentProfiles(): array
    {
        $stmt = $this->pdo->prepare('SELECT id, name, type, options FROM assignment_profile');
        $stmt->execute();
        $results = $stmt->fetchAll(PDO::FETCH_ASSOC);

        if (!$results) {
            return [];
        }

        return array_map(fn(array $result): AssignmentProfile => new AssignmentProfile(
            (int)$result['id'],
            $result['name'],
            ProfileType::from($result['type']),
            json_decode($result['options'], true),
        ), $results);
    }

    /**
     * Získá profil zadání podle ID.
     *
     * @param int $id ID profilu zadání
     * @return AssignmentProfile|null objekt profilu nebo null, pokud neexistuje
     */
    public function getAssignmentProfileById(int $id): ?AssignmentProfile
    {

        $stmt = $this->pdo->prepare('SELECT id, name, type, options FROM assignment_profile WHERE id = :id');
        $stmt->bindValue(':id', $id);
        $stmt->execute();
        $result = $stmt->fetch(PDO::FETCH_ASSOC);

        if (!$result) {
            return null;
        }

        return new AssignmentProfile(
            (int)$result['id'],
            $result['name'],
            ProfileType::from($result['type']),
            json_decode($result['options'], true),
        );
    }

    /**
     * Zapíše do databáze záznam aktivity.
     *
     * @param string $message zpráva popisující aktivitu
     * @param LogType $logType typ aktivity
     * @param int|null $userId ID vyučujícího nebo administrátora, který akci vykonal, nebo null
     * @param int|null $studentId ID studenta, který akci vykonal, nebo null
     */
    public function log(string $message, LogType $logType = LogType::UNKNOWN, ?int $userId = null, ?int $studentId = null): void
    {
        if ($userId === null && $studentId === null) {
            throw new \InvalidArgumentException('Both userId and studentId is null');
        }

        $stmt = $this->pdo->prepare('INSERT INTO logs(time, user_id, student_id, message, log_type) VALUES (:time, :userId, :studentId, :message, :log_type)');
        $stmt->bindValue(':time', date('Y-m-d H:i:s'));
        $stmt->bindValue(':userId', $userId);
        $stmt->bindValue(':studentId', $studentId);
        $stmt->bindValue(':message', $message);
        $stmt->bindValue(':log_type', $logType->value);

        $stmt->execute();
    }

    /**
     * Získá globální nastavení podle klíče.
     *
     * @param string $key klíč nastavení
     * @return string|null hodnota nebo null, pokud hodnota neexistuje
     */
    public function getOption(string $key): ?string
    {
        $stmt = $this->pdo->prepare('SELECT value FROM options WHERE option = :key');
        $stmt->bindValue(':key', $key);
        $stmt->execute();

        $val = $stmt->fetchColumn();

        return is_string($val) && strlen($val) ? (string)$val : null;
    }

    /**
     * Změní globální nastavení.
     *
     * @param string $key klíč nastavení
     * @param string $value nová hodnota
     * @return bool true, pokud se operace podařila, jinak false
     */
    public function setOption(string $key, string $value): bool
    {
        $stmt = $this->pdo->prepare('INSERT INTO options(option, value) VALUES (:key, :value) ON DUPLICATE KEY UPDATE value = :value');
        $stmt->bindValue(':key', $key);
        $stmt->bindValue(':value', $value);
        $stmt->execute();

        try {
            $stmt->execute();
            return true;
        } catch (PDOException) {
            return false;
        }
    }

    /**
     * Získá všechny předměty z daného akademického roku a semestru, kde má vyučující přístup k alespoň jedné rozvrhové akci.
     *
     * @param int $teacherId ID vyučujícího
     * @param int $year akademický rok
     * @param Semester $semester semestr
     * @return Subject[] pole předmětů
     */
    public function getSubjectsByTeacher(int $teacherId, int $year, Semester $semester): array
    {
        $stmt = $this->pdo->prepare('SELECT DISTINCT s.id, s.shortcut, s.name, s.year, s.semester FROM subjects s JOIN scheduled_events e ON e.subject_id=s.id JOIN teachers t ON t.scheduled_event_id=e.id WHERE t.user_id = :teacher_id AND s.year = :year AND s.semester = :semester');
        $stmt->bindValue(':teacher_id', $teacherId);
        $stmt->bindValue(':year', $year);
        $stmt->bindValue(':semester', $semester->value);
        $stmt->execute();

        $results = $stmt->fetchAll(PDO::FETCH_ASSOC);
        if (!$results) {
            return [];
        }

        return array_map(fn(array $result): Subject => new Subject(
            (int)$result['id'],
            $result['shortcut'],
            $result['name'],
            (int)$result['year'],
            Semester::from($result['semester']),
        ), $results);
    }

    /**
     * Získá všechny rozvrhové akce podle předmětu a vyučujícího.
     *
     * @param int $teacherId ID vyučujícího
     * @param int $subjectId ID předmětu
     * @return ScheduledEvent[] pole všech rozvrhových akcí daného předmětu, ke kterým má vyučující přístup
     */
    public function getScheduledEventsByTeacherAndSubject(int $teacherId, int $subjectId): array
    {
        $stmt = $this->pdo->prepare('SELECT e.id, e.subject_id, e.day, e.time_from, e.time_to, e.exam, e.exam_date FROM scheduled_events e JOIN teachers t ON t.scheduled_event_id=e.id WHERE t.user_id = :teacher_id AND e.subject_id = :subject_id ORDER BY e.exam ASC, e.day ASC, e.time_from ASC');
        $stmt->bindValue(':teacher_id', $teacherId);
        $stmt->bindValue(':subject_id', $subjectId);
        $stmt->execute();

        $results = $stmt->fetchAll(PDO::FETCH_ASSOC);
        if (!$results) {
            return [];
        }

        return array_map(fn(array $result): ScheduledEvent => new ScheduledEvent(
            (int)$result['id'],
            (int)$result['subject_id'],
            (int)$result['day'],
            $result['time_from'],
            $result['time_to'],
            ((int) $result['exam']) === 1,
            $result['exam_date'] ? new DateTime($result['exam_date']) : null,
        ), $results);
    }

    /**
     * Získá všechny studenty na dané rozvrhové akci.
     *
     * @param int $scheduledEventId ID rozvrhové akce
     * @return Student[] pole všech studentů na rozvrhové akci
     */
    public function getStudentsByScheduledEvent(int $scheduledEventId): array
    {
        $stmt = $this->pdo->prepare('SELECT id, student_number, orion, name, surname FROM students WHERE scheduled_event_id = :scheduled_event_id ORDER BY surname');
        $stmt->bindValue(':scheduled_event_id', $scheduledEventId);
        $stmt->execute();

        $results = $stmt->fetchAll(PDO::FETCH_ASSOC);
        if (!$results) {
            return [];
        }

        return array_map(fn(array $result): Student => new Student(
            (int)$result['id'],
            $result['student_number'],
            $scheduledEventId,
            $result['orion'],
            $result['name'],
            $result['surname'],
        ), $results);
    }

    /**
     * Získá všechny studenty jiných rozvrhových akcí, kteří byli přiřazení k danému termínu.
     *
     * @param int $scheduledEventId ID rozvrhové akce (termínu)
     * @return Student[] pole všech přiřazených studentů
     */
    public function getStudentsAssignedToExam(int $scheduledEventId): array
    {
        $stmt = $this->pdo->prepare('SELECT s.id, s.scheduled_event_id, s.student_number, s.orion, s.name, s.surname FROM students_on_exam soe JOIN students s ON s.id=soe.student_id WHERE soe.scheduled_event_id = :scheduled_event_id ORDER BY s.surname');
        $stmt->bindValue(':scheduled_event_id', $scheduledEventId);
        $stmt->execute();

        $results = $stmt->fetchAll(PDO::FETCH_ASSOC);
        if (!$results) {
            return [];
        }

        return array_map(fn(array $result): Student => new Student(
            (int)$result['id'],
            $result['student_number'],
            (int) $result['scheduled_event_id'],
            $result['orion'],
            $result['name'],
            $result['surname'],
        ), $results);
    }

    /**
     * Získá ID všech studentů jiných rozvrhových akcí, kteří byli přiřazení k danému termínu.
     *
     * @param int $scheduledEventId ID rozvrhové akce (termínu)
     * @return int[] pole ID všech přiřazených studentů
     */
    public function getStudentsAssignedToExamIds(int $scheduledEventId): array
    {
        $stmt = $this->pdo->prepare('SELECT student_id FROM students_on_exam WHERE scheduled_event_id = :scheduled_event_id');
        $stmt->bindValue(':scheduled_event_id', $scheduledEventId);
        $stmt->execute();

        $results = $stmt->fetchAll(PDO::FETCH_ASSOC);
        if (!$results) {
            return [];
        }

        return array_map(fn(array $result): int => (int) $result['student_id'], $results);
    }

    /**
     * Přiřadí studenta k rozvrhové akci (termínu).
     *
     * @param int $scheduledEventId ID rozvrhové akce
     * @param int $studentId ID studenta
     * @return bool true, pokud se operace podařila, jinak false
     */
    public function addStudentToExam(int $scheduledEventId, int $studentId): bool
    {
        $stmt = $this->pdo->prepare('INSERT INTO students_on_exam(scheduled_event_id, student_id) VALUES (:scheduled_event_id, :student_id)');
        $stmt->bindValue(':scheduled_event_id', $scheduledEventId);
        $stmt->bindValue(':student_id', $studentId);

        try {
            $stmt->execute();
            return true;
        } catch (\Exception) {
            return false;
        }
    }

    /**
     * Odebere přiřazení studenta k rozvrhové akci (termínu).
     *
     * @param int $scheduledEventId ID rozvrhové akce
     * @param int $studentId ID studenta
     * @return bool true, pokud se operace podařila, jinak false
     */
    public function removeStudentFromExam(int $scheduledEventId, int $studentId): bool
    {
        $stmt = $this->pdo->prepare('DELETE FROM students_on_exam WHERE scheduled_event_id = :scheduled_event_id AND student_id = :student_id');
        $stmt->bindValue(':scheduled_event_id', $scheduledEventId);
        $stmt->bindValue(':student_id', $studentId);

        try {
            $stmt->execute();
            return true;
        } catch (\Exception) {
            return false;
        }
    }

    /**
     * Získá studenta podle ID.
     *
     * @param int $id ID studenta
     * @return Student|null objekt studenta nebo null, pokud neexistuje
     */
    public function getStudentById(int $id): ?Student
    {
        $stmt = $this->pdo->prepare('SELECT student_number, scheduled_event_id, orion, name, surname FROM students WHERE id = :id');
        $stmt->bindValue(':id', $id);
        $stmt->execute();

        $result = $stmt->fetch(PDO::FETCH_ASSOC);
        if (!$result) {
            return null;
        }

        return new Student(
            $id,
            $result['student_number'],
            (int)$result['scheduled_event_id'],
            $result['orion'],
            $result['name'],
            $result['surname'],
        );
    }

    /**
     * Získá studenta daného akademického roku a semestru podle jeho orion loginu a osobního čísla.
     *
     * @param string $orion orion login
     * @param string $studentNumber osobní číslo
     * @param int $year akademický rok
     * @param Semester $semester semestr
     * @return Student|null objekt studenta nebo null, pokud neexistuje
     */
    public function getStudentByOrionAndStudentNumber(string $orion, string $studentNumber, int $year, Semester $semester): ?Student
    {
        $stmt = $this->pdo->prepare('SELECT st.id, st.scheduled_event_id, st.name, st.surname FROM students st JOIN scheduled_events e ON e.id=st.scheduled_event_id JOIN subjects s ON s.id=e.subject_id WHERE st.orion = :orion AND st.student_number = :student_number AND s.year = :year AND s.semester = :semester');
        $stmt->bindValue(':orion', $orion);
        $stmt->bindValue(':student_number', $studentNumber);
        $stmt->bindValue(':year', $year);
        $stmt->bindValue(':semester', $semester->value);
        $stmt->execute();
        $result = $stmt->fetch(PDO::FETCH_ASSOC);
        if (!$result) {
            return null;
        }

        return new Student(
            (int)$result['id'],
            $studentNumber,
            (int)$result['scheduled_event_id'],
            $orion,
            $result['name'],
            $result['surname'],
        );
    }

    /**
     * Získá studenta daného akademického roku a semestru podle osobního čísla.
     *
     * @param string $studentNumber osobní číslo
     * @param int $year akademický rok
     * @param Semester $semester semestr
     * @return Student|null objekt studenta nebo null, pokud neexistuje
     */
    public function getStudentByStudentNumber(string $studentNumber, int $year, Semester $semester): ?Student
    {
        $stmt = $this->pdo->prepare('SELECT st.id, st.scheduled_event_id, st.name, st.surname, st.orion FROM students st JOIN scheduled_events e ON e.id=st.scheduled_event_id JOIN subjects s ON s.id=e.subject_id WHERE st.student_number = :student_number AND s.year = :year AND s.semester = :semester');
        $stmt->bindValue(':student_number', $studentNumber);
        $stmt->bindValue(':year', $year);
        $stmt->bindValue(':semester', $semester->value);
        $stmt->execute();
        $result = $stmt->fetch(PDO::FETCH_ASSOC);
        if (!$result) {
            return null;
        }

        return new Student(
            (int)$result['id'],
            $studentNumber,
            (int)$result['scheduled_event_id'],
            $result['orion'],
            $result['name'],
            $result['surname'],
        );
    }

    /**
     * Zjistí, jestli v daný akademický rok a semestr existuje student s daným orion loginem.
     *
     * @param string $orion orion login
     * @param int $year akademický rok
     * @param Semester $semester semestr
     * @return bool true, pokud student existuje, jinak false
     */
    public function checkIfOrionLoginIsUsed(string $orion, int $year, Semester $semester): bool
    {
        $stmt = $this->pdo->prepare('SELECT COUNT(*) FROM students st JOIN scheduled_events e ON e.id=st.scheduled_event_id JOIN subjects s ON s.id=e.subject_id WHERE st.orion = :orion AND s.year = :year AND s.semester = :semester');
        $stmt->bindValue(':orion', $orion);
        $stmt->bindValue(':year', $year);
        $stmt->bindValue(':semester', $semester->value);
        $stmt->execute();
        return (bool)$stmt->fetchColumn();
    }

    /**
     * Zjistí, jestli v daný akademický rok a semestr existuje student s daným osobním číslem.
     *
     * @param string $studentNumber osobní číslo
     * @param int $year akademický rok
     * @param Semester $semester semestr
     * @return bool true, pokud student existuje, jinak false
     */
    public function checkIfStudentNumberLoginIsUsed(string $studentNumber, int $year, Semester $semester): bool
    {
        $stmt = $this->pdo->prepare('SELECT COUNT(*) FROM students st JOIN scheduled_events e ON e.id=st.scheduled_event_id JOIN subjects s ON s.id=e.subject_id WHERE st.student_number = :student_number AND s.year = :year AND s.semester = :semester');
        $stmt->bindValue(':student_number', $studentNumber);
        $stmt->bindValue(':year', $year);
        $stmt->bindValue(':semester', $semester->value);
        $stmt->execute();
        return (bool)$stmt->fetchColumn();
    }

    /**
     * Vytvoří nového studenta.
     *
     * @param int $scheduledEventId ID rozvrhové akce
     * @param string $studentNumber osobní číslo
     * @param string $orion orion login
     * @param string $name jméno
     * @param string $surname příjmení
     * @return int|false ID studenta nebo false při neúspěchu
     */
    public function createStudent(int $scheduledEventId, string $studentNumber, string $orion, string $name, string $surname): int|false
    {
        $stmt = $this->pdo->prepare('INSERT INTO students(student_number, scheduled_event_id, orion, name, surname) VALUES (:student_number, :scheduled_event_id, :orion, :name, :surname)');
        $stmt->bindValue(':student_number', $studentNumber);
        $stmt->bindValue(':scheduled_event_id', $scheduledEventId);
        $stmt->bindValue(':orion', $orion);
        $stmt->bindValue(':name', $name);
        $stmt->bindValue(':surname', $surname);

        try {
            $stmt->execute();
        } catch (PDOException) {
            return false;
        }

        return (int)$this->pdo->lastInsertId();
    }

    /**
     * Upraví studenta.
     *
     * @param int $studentId ID studenta
     * @param string $studentNumber osobní číslo
     * @param string $orion orion login
     * @param string $name jméno
     * @param string $surname příjmení
     * @return bool true, pokud se operace podařila, jinak false
     */
    public function updateStudent(int $studentId, string $studentNumber, string $orion, string $name, string $surname): bool
    {
        $stmt = $this->pdo->prepare('UPDATE students SET student_number = :student_number, orion = :orion, name = :name, surname = :surname WHERE id = :id');
        $stmt->bindValue(':id', $studentId);
        $stmt->bindValue(':student_number', $studentNumber);
        $stmt->bindValue(':orion', $orion);
        $stmt->bindValue(':name', $name);
        $stmt->bindValue(':surname', $surname);

        try {
            $stmt->execute();
        } catch (PDOException) {
            return false;
        }

        return true;
    }

    /**
     * Získá všechna zadání vytvořené pro danou rozvrhovou akci.
     *
     * @param int $scheduledEventId ID rozvrhové akce
     * @return Assignment[] pole zadání
     */
    public function getAllAssignmentsByEvent(int $scheduledEventId): array
    {
        $stmt = $this->pdo->prepare('SELECT id, assignment_profile_id, date_from, date_to, name FROM assignments WHERE scheduled_event_id = :scheduled_event_id ORDER BY date_from');
        $stmt->bindValue(':scheduled_event_id', $scheduledEventId);
        $stmt->execute();

        $results = $stmt->fetchAll(PDO::FETCH_ASSOC);
        if (!$results) {
            return [];
        }

        return array_map(fn(array $result): Assignment => new Assignment(
            (int)$result['id'],
            (int)$result['assignment_profile_id'],
            new DateTime($result['date_from']),
            new DateTime($result['date_to']),
            $scheduledEventId,
            $result['name'],
        ), $results);
    }

    /**
     * Získá zadání podle ID.
     *
     * @param int $id ID zadání
     * @return Assignment|null objekt zadání nebo null, pokud neexistuje
     */
    public function getAssignmentById(int $id): ?Assignment
    {
        $stmt = $this->pdo->prepare('SELECT assignment_profile_id, date_from, date_to, scheduled_event_id, name FROM assignments WHERE id = :id');
        $stmt->bindValue(':id', $id);
        $stmt->execute();

        $result = $stmt->fetch(PDO::FETCH_ASSOC);
        if (!$result) {
            return null;
        }

        return new Assignment(
            $id,
            (int)$result['assignment_profile_id'],
            new DateTime($result['date_from']),
            new DateTime($result['date_to']),
            (int)$result['scheduled_event_id'],
            $result['name'],
        );
    }

    /**
     * Vytvoří nové zadání.
     *
     * @param int $scheduledEventId ID rozvrhové akce
     * @param int $profileId ID profilu zadání
     * @param DateTime $dateFrom datum zveřejnění zadání
     * @param DateTime $dateTo mezní termín odevzdání
     * @param string $name název zadání
     * @return int|false ID zadání nebo false při neúspěchu
     */
    public function createAssignment(int $scheduledEventId, int $profileId, DateTime $dateFrom, DateTime $dateTo, string $name): int|false
    {
        $stmt = $this->pdo->prepare('INSERT INTO assignments(assignment_profile_id, date_from, date_to, scheduled_event_id, name) VALUES (:assignment_profile_id, :date_from, :date_to, :scheduled_event_id, :name)');
        $stmt->bindValue(':assignment_profile_id', $profileId);
        $stmt->bindValue(':date_from', $dateFrom->format('Y-m-d H:i:s'));
        $stmt->bindValue(':date_to', $dateTo->format('Y-m-d H:i:s'));
        $stmt->bindValue(':scheduled_event_id', $scheduledEventId);
        $stmt->bindValue(':name', $name);

        try {
            $stmt->execute();
        } catch (PDOException) {
            return false;
        }

        return (int)$this->pdo->lastInsertId();
    }

    /**
     * Upraví zadání.
     *
     * @param int $assignmentId ID zadání
     * @param int $profileId ID profilu zadání
     * @param DateTime $dateFrom datum zveřejnění zadání
     * @param DateTime $dateTo mezní termín odevzdání
     * @param string $name název zadání
     * @return bool true, pokud se operace podařila, jinak false
     */
    public function updateAssignment(int $assignmentId, int $profileId, DateTime $dateFrom, DateTime $dateTo, string $name): bool
    {
        $stmt = $this->pdo->prepare('UPDATE assignments SET assignment_profile_id = :assignment_profile_id, date_from = :date_from, date_to = :date_to, name = :name WHERE id = :id');
        $stmt->bindValue(':id', $assignmentId);
        $stmt->bindValue(':assignment_profile_id', $profileId);
        $stmt->bindValue(':date_from', $dateFrom->format('Y-m-d H:i:s'));
        $stmt->bindValue(':date_to', $dateTo->format('Y-m-d H:i:s'));
        $stmt->bindValue(':name', $name);

        try {
            $stmt->execute();
        } catch (PDOException) {
            return false;
        }

        return true;
    }

    /**
     * Přiřadí studenta k zadání
     *
     * @param int $assignmentId ID zadání
     * @param int $studentId ID studenta
     * @return bool true, pokud se operace podařila, jinak false
     */
    public function addStudentToAssignment(int $assignmentId, int $studentId): bool
    {
        $stmt = $this->pdo->prepare('INSERT INTO assignment_students(assignment_id, student_id, result) VALUES (:assignment_id, :student_id, \'\')');
        $stmt->bindValue(':assignment_id', $assignmentId);
        $stmt->bindValue(':student_id', $studentId);

        try {
            $stmt->execute();
        } catch (PDOException) {
            return false;
        }

        return true;
    }

    /**
     * Odebere přiřazení studenta k zadání
     *
     * @param int $assignmentId ID zadání
     * @param int $studentId ID studenta
     * @return bool true, pokud se operace podařila, jinak false
     */
    public function removeStudentFromAssignment(int $assignmentId, int $studentId): bool
    {
        $stmt = $this->pdo->prepare('DELETE FROM assignment_students WHERE assignment_id = :assignment_id AND student_id = :student_id');
        $stmt->bindValue(':assignment_id', $assignmentId);
        $stmt->bindValue(':student_id', $studentId);

        try {
            $stmt->execute();
        } catch (PDOException) {
            return false;
        }

        return true;
    }

    /**
     * Nastaví, že studentovo zadání bylo vygenerováno. Student musí mít zadání přiřazené.
     *
     * @param int $assignmentId ID zadání
     * @param int $studentId ID studenta
     * @return bool true, pokud se operace podařila, jinak false
     */
    public function setAssignmentGenerated(int $assignmentId, int $studentId): bool
    {
        $stmt = $this->pdo->prepare('UPDATE assignment_students SET generated = 1, state = :state WHERE assignment_id = :assignment_id AND student_id = :student_id');
        $stmt->bindValue(':assignment_id', $assignmentId);
        $stmt->bindValue(':student_id', $studentId);
        $stmt->bindValue(':state', AssignmentState::NEW->value);

        try {
            $stmt->execute();
        } catch (PDOException) {
            return false;
        }

        return true;
    }

    /**
     * Získá vazbu mezi zadáním a studentem.
     *
     * @param int $assignmentId ID zadání
     * @param int $studentId ID studenta
     * @return AssignmentStudent|null objekt představující vazbu mezi studentem a zadáním nebo null, pokud neexistuje
     */
    public function getStudentAssignmentDetails(int $assignmentId, int $studentId): ?AssignmentStudent
    {
        $stmt = $this->pdo->prepare(<<<SQL
            SELECT ast.generated, ast.state, ast.result, 
                   (SELECT COUNT(*) FROM assignment_files af WHERE af.assignment_id = ast.assignment_id AND af.student_id = ast.student_id AND af.filetype = :filetype) AS attempts 
            FROM assignment_students ast
            WHERE ast.assignment_id = :assignment_id AND ast.student_id = :student_id
            SQL
        );
        $stmt->bindValue(':assignment_id', $assignmentId);
        $stmt->bindValue(':student_id', $studentId);
        $stmt->bindValue(':filetype', FileType::UPLOAD->value);
        $stmt->execute();

        $result = $stmt->fetch(PDO::FETCH_ASSOC);
        if (!$result) {
            return null;
        }

        return new AssignmentStudent(
            $assignmentId,
            $studentId,
            ((int)$result['generated']) === 1,
            AssignmentState::from($result['state']),
            $result['result'],
            (int)$result['attempts'],
        );
    }

    /**
     * Získá všechny vazby daného zadání na studenty.
     *
     * @param int $assignmentId ID zadání
     * @return AssignmentStudent[] pole vazeb mezi studentem a zadáním
     */
    public function getStudentAssignmentsWithoutFiles(int $assignmentId): array
    {
        $stmt = $this->pdo->prepare('SELECT student_id, state, result FROM assignment_students WHERE assignment_id = :assignment_id AND generated = 0');
        $stmt->bindValue(':assignment_id', $assignmentId);
        $stmt->execute();

        $results = $stmt->fetchAll(PDO::FETCH_ASSOC);
        if (!$results) {
            return [];
        }

        return array_map(fn(array $result): AssignmentStudent => new AssignmentStudent(
            $assignmentId,
            (int)$result['student_id'],
            false,
            AssignmentState::from($result['state']),
            $result['result'],
            0,
        ), $results);
    }

    /**
     * Získá všechny vazby daného studenta na zadání.
     *
     * @param int $studentId ID studenta
     * @return FullAssignmentStudent[] pole vazeb studenta na zadání obohacené o popis zadání a počet pokusů odevzdání
     */
    public function getPublishedStudentAssignments(int $studentId): array
    {
        $stmt = $this->pdo->prepare(<<<SQL
            SELECT ast.assignment_id, a.date_from, a.date_to, a.name, ast.generated, ast.state, ast.result,
                   (SELECT COUNT(*) FROM assignment_files af WHERE af.assignment_id = ast.assignment_id AND af.student_id = ast.student_id AND af.filetype = :filetype) AS attempts
            FROM assignment_students ast 
            JOIN assignments a ON a.id=ast.assignment_id 
            WHERE ast.student_id = :student_id 
            ORDER BY a.date_from ASC
            SQL
        );
        $stmt->bindValue(':student_id', $studentId);
        $stmt->bindValue(':filetype', FileType::UPLOAD->value);
        $stmt->execute();

        $results = $stmt->fetchAll(PDO::FETCH_ASSOC);
        if (!$results) {
            return [];
        }

        return array_map(fn(array $result): FullAssignmentStudent => new FullAssignmentStudent(
            (int)$result['assignment_id'],
            new DateTime($result['date_from']),
            new DateTime($result['date_to']),
            $result['name'],
            $studentId,
            ((int)$result['generated']) === 1,
            AssignmentState::from($result['state']),
            $result['result'],
            (int)$result['attempts'],
        ), $results);
    }

    /**
     * Vytvoří záznam popisující nahraný soubor přiřazený k zadání a studentovi.
     *
     * @param int $assignmentId ID zadání
     * @param int $studentId ID studenta
     * @param string $filename název souboru
     * @param FileType $fileType typ souboru (vygenerovaný, nahraný apod.)
     * @param string $location fyzické umístění souboru
     * @return int|false ID nahraného souboru nebo false při neúspěchu
     */
    public function addAssignmentFile(int $assignmentId, int $studentId, string $filename, FileType $fileType, string $location): int|false
    {
        $stmt = $this->pdo->prepare('INSERT INTO assignment_files(assignment_id, student_id, filename, filetype, location) VALUES (:assignment_id, :student_id, :filename, :filetype, :location)');
        $stmt->bindValue(':assignment_id', $assignmentId);
        $stmt->bindValue(':student_id', $studentId);
        $stmt->bindValue(':filename', $filename);
        $stmt->bindValue(':filetype', $fileType->value);
        $stmt->bindValue(':location', $location);

        try {
            $stmt->execute();
        } catch (PDOException) {
            return false;
        }

        return (int)$this->pdo->lastInsertId();
    }

    /**
     * Získá všechny soubory přiřazené k danému zadání a studentovi. Pokud se jedná o výsledek pro studenty, vrátí se pouze vstupní soubory, textový popis zadání a náhled.
     *
     * @param int $assignmentId ID zadání
     * @param int $studentId ID studenta
     * @param bool $forStudent true, pokud je výsledek určen pro studenty, jinak false
     * @return AssignmentFile[] pole všech souborů k zadání
     */
    public function getStudentAssignmentFiles(int $assignmentId, int $studentId, bool $forStudent = false): array
    {
        $stmt = $this->pdo->prepare(
            'SELECT id, filename, filetype, location, `time` FROM assignment_files WHERE assignment_id = :assignment_id AND student_id = :student_id'
            . ($forStudent === true ? ' AND filetype IN (' . implode(',', [FileType::INPUT->value, FileType::ASSIGNMENT_TXT->value, FileType::PREVIEW->value]) . ')' : ' ORDER BY time DESC, id ASC')
        );
        $stmt->bindValue(':assignment_id', $assignmentId);
        $stmt->bindValue(':student_id', $studentId);
        $stmt->execute();

        $results = $stmt->fetchAll(PDO::FETCH_ASSOC);
        if (!$results) {
            return [];
        }

        return array_map(fn(array $result): AssignmentFile => new AssignmentFile(
            (int)$result['id'],
            $assignmentId,
            $studentId,
            $result['filename'],
            FileType::from($result['filetype']),
            $result['location'],
            new DateTime($result['time']),
        ), $results);
    }

    /**
     * Získá všechny soubory k danému zadání.
     *
     * @param int $assignmentId ID zadání
     * @return AssignmentFile[] pole všech souborů k danému zadání
     */
    public function getAllAssignmentFiles(int $assignmentId): array
    {
        $stmt = $this->pdo->prepare('SELECT id, student_id, filename, filetype, location, `time` FROM assignment_files WHERE assignment_id = :assignment_id');
        $stmt->bindValue(':assignment_id', $assignmentId);
        $stmt->execute();

        $results = $stmt->fetchAll(PDO::FETCH_ASSOC);
        if (!$results) {
            return [];
        }

        return array_map(fn(array $result): AssignmentFile => new AssignmentFile(
            (int)$result['id'],
            $assignmentId,
            (int)$result['student_id'],
            $result['filename'],
            FileType::from($result['filetype']),
            $result['location'],
            new DateTime($result['time']),
        ), $results);
    }

    /**
     * Získá soubor zadání podle ID.
     *
     * @param int $id ID souboru zadání
     * @return AssignmentFile|null daný soubor zadání nebo null, pokud neexistuje
     */
    public function getAssignmentFileById(int $id): ?AssignmentFile
    {
        $stmt = $this->pdo->prepare('SELECT assignment_id, student_id, filename, filetype, location, `time` FROM assignment_files WHERE id = :id');
        $stmt->bindValue(':id', $id);
        $stmt->execute();

        $result = $stmt->fetch(PDO::FETCH_ASSOC);
        if (!$result) {
            return null;
        }

        return new AssignmentFile(
            $id,
            (int)$result['assignment_id'],
            (int)$result['student_id'],
            $result['filename'],
            FileType::from($result['filetype']),
            $result['location'],
            new DateTime($result['time']),
        );
    }

    /**
     * Smaže soubor zadání z databáze.
     *
     * @param int $id ID souboru zadání
     * @return bool true, pokud se operace podařila, jinak false
     */
    public function removeAssignmentFile(int $id): bool
    {
        $stmt = $this->pdo->prepare('DELETE FROM assignment_files WHERE id = :id');
        $stmt->bindValue(':id', $id);

        try {
            $stmt->execute();
        } catch (PDOException) {
            return false;
        }

        return true;
    }

    /**
     * Získá počet všech záznamů aktivit podle zadaných filtrů.
     *
     * @param int|null $studentId ID studenta
     * @param string|null $searchUser část jména uživatele, který akci vykonal
     * @param string|null $searchText část zprávy popisující aktivitu
     * @param LogType|null $searchType prohledávaný typ aktivity
     * @return int počet záznamů
     */
    public function getLogCount(?int $studentId = null, ?string $searchUser = null, ?string $searchText = null, ?LogType $searchType = null): int
    {
        $stmt = $this->pdo->prepare(
            'SELECT COUNT(*) FROM logs l' .
            ($searchUser !== null ? ' LEFT JOIN users u ON u.id=l.user_id LEFT JOIN students s ON s.id=l.student_id ' : '') .
            ($studentId !== null || $searchText !== null || $searchType !== null || $searchUser !== null ? ' WHERE ' : '') .
            implode(' AND ', array_filter([
                ($studentId !== null ? 'l.student_id = :student_id' : null),
                ($searchText !== null ? 'l.message LIKE :search' : null),
                ($searchType !== null ? 'l.log_type = :type' : null),
                ($searchUser !== null ? '(u.username LIKE :search_user OR s.orion LIKE :search_user)' : null),
            ])));
        if ($studentId !== null) {
            $stmt->bindValue(':student_id', $studentId);
        }
        if ($searchText !== null) {
            $stmt->bindValue(':search', '%' . $searchText . '%');
        }
        if ($searchType !== null) {
            $stmt->bindValue(':type', $searchType->value);
        }
        if ($searchUser !== null) {
            $stmt->bindValue(':search_user', '%' . $searchUser . '%');
        }
        $stmt->execute();

        return (int)$stmt->fetchColumn();
    }

    /**
     * Získá všechny záznamů aktivit podle zadaných filtrů a stránky.
     *
     * @param int $page stránka
     * @param int $limit počet položek na stránku
     * @param int|null $studentId ID studenta
     * @param string|null $searchUser část jména uživatele, který akci vykonal
     * @param string|null $searchText část zprávy popisující aktivitu
     * @param LogType|null $searchType prohledávaný typ aktivity
     * @return Log[] pole záznamů aktivit
     */
    public function getLogs(int $page, int $limit, ?int $studentId = null, ?string $searchUser = null, ?string $searchText = null, ?LogType $searchType = null): array
    {
        $stmt = $this->pdo->prepare('
        SELECT l.id, l.time, l.user_id, COALESCE(u.username, s.orion) AS user_name, l.student_id, l.message, l.log_type 
        FROM logs l 
            LEFT JOIN users u ON u.id=l.user_id 
            LEFT JOIN students s ON s.id=l.student_id
        ' . ($studentId !== null || $searchText !== null || $searchType !== null || $searchUser !== null ? ' WHERE ' : '') . '
        ' . implode(' AND ', array_filter([
                ($studentId !== null ? 'l.student_id = :student_id' : null),
                ($searchText !== null ? 'l.message LIKE :search' : null),
                ($searchType !== null ? 'l.log_type = :type' : null),
                ($searchUser !== null ? '(u.username LIKE :search_user OR s.orion LIKE :search_user)' : null),
            ])) . '
        ORDER BY l.time DESC
        LIMIT :limit 
        OFFSET :offset');
        if ($studentId !== null) {
            $stmt->bindValue(':student_id', $studentId);
        }
        if ($searchText !== null) {
            $stmt->bindValue(':search', '%' . $searchText . '%');
        }
        if ($searchType !== null) {
            $stmt->bindValue(':type', $searchType->value);
        }
        if ($searchUser !== null) {
            $stmt->bindValue(':search_user', '%' . $searchUser . '%');
        }
        $stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
        $stmt->bindValue(':offset', ($page - 1) * $limit, PDO::PARAM_INT);
        $stmt->execute();

        $results = $stmt->fetchAll(PDO::FETCH_ASSOC);
        if (!$results) {
            return [];
        }

        return array_map(fn(array $result): Log => new Log(
            (int)$result['id'],
            new DateTime($result['time']),
            (int)$result['user_id'],
            (int)$result['student_id'],
            $result['user_name'] ?? 'Smazaný uživatel',
            $result['message'],
            LogType::from((int)$result['log_type']),
        ), $results);
    }

    /**
     * Spočte počet pokusů odevzdání zadání jedním studentem.
     *
     * @param int $assignmentId ID zadání
     * @param int $studentId ID studenta
     * @return int počet pokusů
     */
    public function countStudentAttempts(int $assignmentId, int $studentId): int
    {
        $stmt = $this->pdo->prepare('SELECT COUNT(*) FROM assignment_files WHERE assignment_id = :assignment_id AND student_id = :student_id AND filetype = :filetype');
        $stmt->bindValue(':assignment_id', $assignmentId);
        $stmt->bindValue(':student_id', $studentId);
        $stmt->bindValue(':filetype', FileType::UPLOAD->value);
        $stmt->execute();

        return (int)$stmt->fetchColumn();
    }

    /**
     * Změní hodnocení práce studenta.
     *
     * @param int $studentId ID studenta
     * @param int $assignmentId ID zadání
     * @param AssignmentState $state stav studentova zadání
     * @param string $result komentář vyučujícího k hodnocení
     * @return bool true, pokud se operace podařila, jinak false
     */
    public function updateStudentRating(int $studentId, int $assignmentId, AssignmentState $state, string $result): bool
    {
        $stmt = $this->pdo->prepare('UPDATE assignment_students SET state = :state, result = :result WHERE student_id = :student_id AND assignment_id = :assignment_id');
        $stmt->bindValue(':student_id', $studentId);
        $stmt->bindValue(':assignment_id', $assignmentId);
        $stmt->bindValue(':state', $state->value);
        $stmt->bindValue(':result', $result);

        try {
            $stmt->execute();
        } catch (PDOException) {
            return false;
        }

        return true;
    }

    public function getStudentsFullySubmittedByEvent(int $scheduledEventId): array
    {
        $stmt = $this->pdo->prepare(<<<SQL
            SELECT
                s.id,
                s.student_number,
                s.orion,
                s.name,
                s.surname
            FROM students s
            WHERE s.scheduled_event_id = :event_id
            AND NOT EXISTS (
                SELECT 1
                FROM assignments a
                WHERE a.scheduled_event_id = :event_id
                    AND NOT EXISTS (
                        SELECT 1
                        FROM assignment_files af
                        WHERE af.assignment_id = a.id
                        AND af.student_id = s.id
                        AND af.filetype = :upload_type
                    )
            )
            ORDER BY s.surname, s.name
        SQL);

        $stmt->bindValue(':event_id', $scheduledEventId, PDO::PARAM_INT);
        $stmt->bindValue(':upload_type', FileType::UPLOAD->value, PDO::PARAM_INT);
        $stmt->execute();

        return $stmt->fetchAll(PDO::FETCH_ASSOC) ?: [];
    }

    public function getUploadedAssignmentIdsForStudentOnEvent(int $eventId, int $studentId): array
    {
        $stmt = $this->pdo->prepare(<<<SQL
            SELECT DISTINCT af.assignment_id
            FROM assignment_files af
            JOIN assignments a ON a.id = af.assignment_id
            WHERE a.scheduled_event_id = :event_id
            AND af.student_id = :student_id
            AND af.filetype = :upload_type
        SQL);

        $stmt->bindValue(':event_id', $eventId, PDO::PARAM_INT);
        $stmt->bindValue(':student_id', $studentId, PDO::PARAM_INT);
        $stmt->bindValue(':upload_type', FileType::UPLOAD->value, PDO::PARAM_INT);
        $stmt->execute();

        $rows = $stmt->fetchAll(PDO::FETCH_COLUMN) ?: [];
        return array_map('intval', $rows);
    }

    public function getOverallStateForStudentOnEvent(int $eventId, int $studentId): ?AssignmentState
    {
        $stmt = $this->pdo->prepare(<<<SQL
            SELECT ast.state
            FROM assignment_students ast
            JOIN assignments a ON a.id = ast.assignment_id
            WHERE a.scheduled_event_id = :event_id
            AND ast.student_id = :student_id
        SQL);

        $stmt->bindValue(':event_id', $eventId, PDO::PARAM_INT);
        $stmt->bindValue(':student_id', $studentId, PDO::PARAM_INT);
        $stmt->execute();

        $states = $stmt->fetchAll(PDO::FETCH_COLUMN) ?: [];
        if (!$states) return null;

        $states = array_map('intval', $states);

        if (in_array(AssignmentState::REJECTED->value, $states, true)) {
            return AssignmentState::REJECTED;
        }

        foreach ($states as $s) {
            if ($s !== AssignmentState::ACCEPTED->value) {
                return null; 
            }
        }

        return AssignmentState::ACCEPTED;
    }

    public function getLatestUploadTimeForStudentOnEvent(int $eventId, int $studentId): ?\DateTime
    {
        $stmt = $this->pdo->prepare(<<<SQL
            SELECT MAX(af.time) AS last_time
            FROM assignment_files af
            JOIN assignments a ON a.id = af.assignment_id
            WHERE a.scheduled_event_id = :event_id
            AND af.student_id = :student_id
            AND af.filetype = :upload_type
        SQL);

        $stmt->bindValue(':event_id', $eventId, PDO::PARAM_INT);
        $stmt->bindValue(':student_id', $studentId, PDO::PARAM_INT);
        $stmt->bindValue(':upload_type', FileType::UPLOAD->value, PDO::PARAM_INT);
        $stmt->execute();

        $val = $stmt->fetchColumn();
        if (!$val) return null;

        return new \DateTime((string)$val);
    }

    // pro kongig
    public function getChecksConfigBySubjectId(int $subjectId): ?array
    {
        $row = $this->queryOne(
            "SELECT config_json FROM checks_config WHERE subject_id = ?",
            [$subjectId]
        );

        if (!$row) return null;

        $data = json_decode((string)$row['config_json'], true);
        return is_array($data) ? $data : null;
    }

    public function saveChecksConfigForSubject(int $subjectId, array $text, array $spreadsheet): bool
    {
        $payload = json_encode([
            'text' => $text,
            'spreadsheet' => $spreadsheet,
        ], JSON_UNESCAPED_UNICODE);

        $sql = "
            INSERT INTO checks_config (subject_id, config_json)
            VALUES (?, ?)
            ON DUPLICATE KEY UPDATE config_json = VALUES(config_json)
        ";

        $stmt = $this->pdo->prepare($sql);
        return $stmt->execute([$subjectId, $payload]);
    }

    public function getAllCheckDefinitions(string $type): array
    {
         $registryPath = '/bp/checks_config/checks_registry.json';

        if (!is_file($registryPath)) {
            return [];
        }

        $data = json_decode((string) file_get_contents($registryPath), true);
        if (!is_array($data)) {
            return [];
        }

        $items = $data[$type] ?? null;
        if (!is_array($items)) {
            return [];
        }

        $out = [];
        foreach ($items as $row) {
            if (!is_array($row)) continue;

            $code = isset($row['code']) && is_string($row['code']) ? trim($row['code']) : '';
            if ($code === '') continue;

            $out[] = [
                'code' => $code,
                'title' => isset($row['title']) && is_string($row['title']) ? $row['title'] : '',
                'default_enabled' => array_key_exists('default_enabled', $row) ? (bool)$row['default_enabled'] : true,
                'order' => array_key_exists('order', $row) ? (int)$row['order'] : 0,
            ];
        }

        return $out;
    }

    private function queryOne(string $sql, array $params = []): ?array
    {
        $stmt = $this->pdo->prepare($sql);
        $stmt->execute($params);

        $row = $stmt->fetch(\PDO::FETCH_ASSOC);
        return $row !== false ? $row : null;
    }

    public function getSubjectIdByAssignmentId(int $assignmentId): ?int
    {
        $row = $this->queryOne(
            "SELECT se.subject_id
            FROM assignments a
            JOIN scheduled_events se ON se.id = a.scheduled_event_id
            WHERE a.id = ?",
            [$assignmentId]
        );

        return $row ? (int)$row['subject_id'] : null;
    }
}