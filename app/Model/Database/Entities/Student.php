<?php

declare(strict_types=1);

namespace App\Model\Database\Entities;

/**
 * Třída reprezentující studenta vráceného z databáze.
 *
 * @author Michal Turek
 */
readonly class Student
{
    /**
     * @param int $id ID studenta
     * @param string $studentNumber Studentské číslo, unikátní v rámci ročníku a semestru
     * @param int $scheduledEventId ID rozvrhové akce
     * @param string $orion Orion login, unikátní v rámci ročníku a semestru
     * @param string $name Jméno
     * @param string $surname Příjmení
     */
    public function __construct(
        public int $id,
        public string $studentNumber,
        public int $scheduledEventId,
        public string $orion,
        public string $name,
        public string $surname,
    ) {
    }
}