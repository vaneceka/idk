<?php

declare(strict_types=1);

namespace App\Model\Database\Entities;

/**
 * Třída reprezentující uživatele (administrátor nebo vyučující) vráceného z databáze.
 *
 * @author Michal Turek
 */
readonly class User
{
    /**
     * @param int $id ID uživatele
     * @param string $username uživatelské jméno
     * @param string $name Jméno
     * @param string $surname Příjmení
     * @param bool $isAdmin true, pokud se jedná o administrátora, jinak false
     */
    public function __construct(
        public int $id,
        public string $username,
        public string $name,
        public string $surname,
        public bool $isAdmin,
    ) {
    }
}