<?php

declare(strict_types=1);

namespace App\Model\Database\Entities;

use DateTime;

/**
 * Třída popisující rozvrhovou akci nebo termín vrácený z databáze.
 *
 * @author Michal Turek
 */
readonly class ScheduledEvent
{
    public string $timeFrom;
    public string $timeTo;

    /**
     * @param int $id ID rozvrhové akce
     * @param int $subjectId ID předmětu
     * @param int $day den v týdnu, od 1 do 7
     * @param string $timeFrom čas začátku rozvrhové akce ve formátu HH:MM
     * @param string $timeTo čas konce rozvrhové akce ve formátu HH:MM
     * @param bool $isExam true, pokud se jedná o termín, jinak false
     * @param DateTime|null $examDate datum termínu, pokud se jedná o termín, jinak null
     */
    public function __construct(
        public int $id,
        public int $subjectId,
        public int $day,
        string $timeFrom,
        string $timeTo,
        public bool $isExam,
        public ?DateTime $examDate,
    ) {
        $this->timeFrom = substr($timeFrom, 0, 5);
        $this->timeTo = substr($timeTo, 0, 5);
    }
}
