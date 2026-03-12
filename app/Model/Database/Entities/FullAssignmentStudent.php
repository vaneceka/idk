<?php

declare(strict_types=1);

namespace App\Model\Database\Entities;

use App\Model\Database\Types\AssignmentState;
use DateTime;

/**
 * Třída reprezentující vazbu mezi studentem a zadáním vrácenou z databáze s přidáním některých dalších údajů z tabulky zadání.
 *
 * @author Michal Turek
 */
readonly class FullAssignmentStudent
{
    /**
     * @param int $assignmentId ID zadání
     * @param DateTime $dateFrom datum zveřejnění zadání
     * @param DateTime $dateTo termín odevzdání
     * @param string $name název zadání
     * @param int $studentId ID studenta
     * @param bool $generated true, pokud již byly soubory zadání vygenerovány, jinak false
     * @param AssignmentState $state stav zadání
     * @param string $result komentář vyučujícího
     * @param int $attempts počet pokusů odevzdání
     */
    public function __construct(
        public int $assignmentId,
        public DateTime $dateFrom,
        public DateTime $dateTo,
        public string $name,
        public int $studentId,
        public bool $generated,
        public AssignmentState $state,
        public string $result,
        public int $attempts,
    ) {
    }
}
