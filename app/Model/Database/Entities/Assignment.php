<?php

declare(strict_types=1);

namespace App\Model\Database\Entities;

use DateTime;

/**
 * Třída reprezentující zadání vrácené z databáze.
 *
 * @author Michal Turek
 */
readonly class Assignment
{
    /**
     * @param int $id ID zadání
     * @param int $assignmentProfileId ID profilu zadání
     * @param DateTime $dateFrom datum zveřejnění zadání
     * @param DateTime $dateTo termín odevzdání
     * @param int $scheduledEventId ID rozvrhové akce nebo termínu
     * @param string $name název zadání
     */
    public function __construct(
        public int $id,
        public int $assignmentProfileId,
        public DateTime $dateFrom,
        public DateTime $dateTo,
        public int $scheduledEventId,
        public string $name,
    ) {
    }
}
