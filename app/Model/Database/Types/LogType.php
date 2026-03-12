<?php

declare(strict_types=1);

namespace App\Model\Database\Types;

/**
 * Výčet reprezentující typ zaznamenávané aktivity.
 *
 * @author Michal Turek
 */
enum LogType: int
{
    /**
     * Blíže nedefinovaná aktivita
     */
    case UNKNOWN = 0;
    /**
     * Přihlášení uživatele
     */
    case LOGIN = 1;
    /**
     * Odhlášení uživatele
     */
    case LOGOUT = 2;
    /**
     * Stažení souboru zadání
     */
    case DOWNLOAD = 3;
    /**
     * Změna globálního nastavení systému
     */
    case OPTIONS = 4;
    /**
     * Vytvoření nového profilu zadání
     */
    case PROFILE_ADD = 5;
    /**
     * Úprava profilu zadání
     */
    case PROFILE_EDIT = 6;
    /**
     * Odebrání profilu zadání
     */
    case PROFILE_DELETE = 7;
    /**
     * Vytvoření nového administrátora/vyučujícího
     */
    case USER_ADD = 8;
    /**
     * Úprava administrátora/vyučujícího
     */
    case USER_EDIT = 9;
    /**
     * Odebrání administrátora/vyučujícího
     */
    case USER_DELETE = 10;
    /**
     * Vytvoření nového předmětu
     */
    case SUBJECT_ADD = 11;
    /**
     * Úprava předmětu
     */
    case SUBJECT_EDIT = 12;
    /**
     * Vytvoření nové rozvrhové akce/zápočtového termínu
     */
    case EVENT_ADD = 13;
    /**
     * Úprava rozvrhové akce/zápočtového termínu
     */
    case EVENT_EDIT = 14;
    /**
     * Vytvoření nového studenta
     */
    case STUDENT_ADD = 15;
    /**
     * Úprava studenta
     */
    case STUDENT_EDIT = 16;
    /**
     * Vytvoření nového zadání
     */
    case ASSIGNMENT_ADD = 17;
    /**
     * Úprava zadání
     */
    case ASSIGNMENT_EDIT = 18;
    /**
     * Přiřazení studenta k zadání
     */
    case ASSIGNMENT_STUDENT_ASSIGN = 19;
    /**
     * Odebrání přiřazení studenta k zadání
     */
    case ASSIGNMENT_STUDENT_DEASSIGN = 20;
    /**
     * Vygenerování souborů zadání
     */
    case ASSIGNMENT_STUDENT_GENERATE = 21;
    /**
     * Odevzdání vypracování
     */
    case SUBMIT = 22;
    /**
     * Ohodnocení odevzdaného zadání
     */
    case RATED = 23;
    /**
     * Změna studentů na zápočtovém termínu
     */
    case EXAM_STUDENTS = 24;

    /**
     * Metoda pro navrácení překladového textu reprezentující daný typ aktivity.
     *
     * @return string překladový text
     */
    public function getName(): string
    {
        return match ($this) {
            self::UNKNOWN => 'Blíže neurčeno',
            self::LOGIN => 'Přihlášení',
            self::LOGOUT => 'Odhlášení',
            self::DOWNLOAD => 'Stažení souboru',
            self::OPTIONS => 'Nastavení systému',
            self::PROFILE_ADD => 'Vytvoření profilu',
            self::PROFILE_EDIT => 'Úprava profilu',
            self::PROFILE_DELETE => 'Smazání profilu',
            self::USER_ADD => 'Vytvoření uživatele',
            self::USER_EDIT => 'Úprava uživatele',
            self::USER_DELETE => 'Smazání uživatele',
            self::SUBJECT_ADD => 'Vytvoření předmětu',
            self::SUBJECT_EDIT => 'Úprava předmětu',
            self::EVENT_ADD => 'Vytvoření rozvrhové akce',
            self::EVENT_EDIT => 'Úprava rozvrhové akce',
            self::STUDENT_ADD => 'Vytvoření studenta',
            self::STUDENT_EDIT => 'Úprava studenta',
            self::ASSIGNMENT_ADD => 'Vytvoření zadání',
            self::ASSIGNMENT_EDIT => 'Úprava zadání',
            self::ASSIGNMENT_STUDENT_ASSIGN => 'Přiřazení zadání studentovi',
            self::ASSIGNMENT_STUDENT_DEASSIGN => 'Odebrání zadání studentovi',
            self::ASSIGNMENT_STUDENT_GENERATE => 'Vygenerování souborů zadání',
            self::SUBMIT => 'Odevzdání vypracování',
            self::RATED => 'Uloženo hodnocení',
            self::EXAM_STUDENTS => 'Změna studentů na termínu',
        };
    }
}
