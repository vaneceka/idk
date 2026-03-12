<?php

declare(strict_types=1);

namespace App\Model\Database\Types;

/**
 * Výčet reprezentující stav zadání jednoho studenta.
 *
 * @author Michal Turek
 */
enum AssignmentState: int
{
    /**
     * Nové zadání
     */
    case NEW = 0;
    /**
     * Splněné zadání
     */
    case ACCEPTED = 1;
    /**
     * Zadání vrácené k přepracování
     */
    case RETURNED = 2;
    /**
     * Zadání bylo zamítnuto a není možné jej odevzdat znovu
     */
    case REJECTED = 3;

    /**
     * Metoda pro navrácení překladového textu reprezentující daný stav.
     *
     * @return string překladový text
     */
    public function getText(): string
    {
        return match ($this) {
            self::NEW => 'Dosud nehodnoceno',
            self::ACCEPTED => 'Přijato',
            self::RETURNED => 'Vráceno k opravě',
            self::REJECTED => 'Zamítnuto',
        };
    }

    /**
     * Metoda pro navrácení css třídy s barevným pozadím.
     *
     * @return string css třída
     */
    public function getColor(): string
    {
        return match ($this) {
            self::NEW => '',
            self::ACCEPTED => 'success',
            self::RETURNED => 'warning',
            self::REJECTED => 'danger',
        };
    }
}

