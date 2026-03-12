<?php

declare(strict_types=1);

namespace App\Model\Database\Entities;

use App\Model\Database\Types\ProfileType;

/**
 * Třída reprezentující profil zadání vrácený z databáze.
 *
 * @author Michal Turek
 */
readonly class AssignmentProfile
{
    /**
     * @param int $id ID profilu zadání
     * @param string $name název profilu zadání
     * @param ProfileType $type typ profilu zadání
     * @param array $options pole obsahující dodatečné nastavení k profilům zadání
     */
    public function __construct(
        public int $id,
        public string $name,
        public ProfileType $type,
        public array $options,
    ) {
    }
}
