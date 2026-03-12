<?php

declare(strict_types=1);

namespace App\Model\Database\Entities;

use App\Model\Database\Types\LogType;
use DateTime;

/**
 * Třída reprezentující záznam v záznamu aktivit vrácený z databáze.
 *
 * @author Michal Turek
 */
readonly class Log
{
    /**
     * @param int $id ID záznamu
     * @param DateTime $time čas záznamu
     * @param int|null $userId ID uživatele, který záznam vyvolal, administrace nebo null
     * @param int|null $studentId ID studenta, který záznam vyvolal, nebo null
     * @param string $userName uživatelské jméno vyučujícího nebo studenta, případně text "Smazaný uživatel"
     * @param string $message Zpráva popisující samotnou událost
     * @param LogType $logType typ záznamu
     */
    public function __construct(
        public int $id,
        public DateTime $time,
        public ?int $userId,
        public ?int $studentId,
        public string $userName,
        public string $message,
        public LogType $logType,
    ) {
    }
}
