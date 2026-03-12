<?php

declare(strict_types=1);

namespace App\Model\Database\Entities;

use App\Model\Database\Types\Semester;

/**
 * Třída reprezentující předmět vrácený z databáze.
 *
 * @author Michal Turek
 */
readonly class Subject
{
    /**
     * @param int $id ID předmětu
     * @param string $shortcut zkratka předmětu včetně katedry
     * @param string $name název předmětu
     * @param int $year akademický rok (jeho první část, tedy pro akademický rok 2024/2025 je hodnota 2024)
     * @param Semester $semester semestr, ve kterém se předmět vyučuje
     */
    public function __construct(
        public int $id,
        public string $shortcut,
        public string $name,
        public int $year,
        public Semester $semester,
    ) {
    }
}