<?php

declare(strict_types=1);

namespace App\Model\Database\Entities;

use App\Model\Database\Types\AssignmentState;

/**
 * Třída reprezentující vazbu mezi studentem a zadáním vrácenou z databáze.
 *
 * @author Michal Turek
 */
readonly class AssignmentStudent
{
    /**
     * @param int $assignmentId ID zadání
     * @param int $studentId ID studenta
     * @param bool $generated true, pokud již byly soubory zadání vygenerovány, jinak false
     * @param AssignmentState $state stav zadání
     * @param string $result komentář vyučujícího
     * @param int $attempts počet pokusů odevzdání
     */
    public function __construct(
        public int $assignmentId,
        public int $studentId,
        public bool $generated,
        public AssignmentState $state,
        public string $result,
        public int $attempts,
    ) {
    }
}
