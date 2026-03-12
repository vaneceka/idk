<?php

declare(strict_types=1);

namespace App\Model\Database\Entities;

use App\Model\Database\Types\FileType;

/**
 * Třída reprezentující soubor k zadání vrácený z databáze.
 *
 * @author Michal Turek
 */
readonly class AssignmentFile
{
    /**
     * @param int $id ID souboru zadání
     * @param int $assignmentId ID zadání
     * @param int $studentId ID studenta
     * @param string $filename název souboru
     * @param FileType $filetype typ souboru (vygenerovaný, nahraný apod.)
     * @param string $location fyzické umístění souboru na disku
     * @param \DateTime $time datum vytvoření
     */
    public function __construct(
        public int $id,
        public int $assignmentId,
        public int $studentId,
        public string $filename,
        public FileType $filetype,
        public string $location,
        public \DateTime $time,
    ) {
    }
}
