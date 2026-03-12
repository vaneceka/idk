<?php

declare(strict_types=1);

namespace App\Model\Database\Types;

/**
 * Výčet představující semestr
 *
 * @author Michal Turek
 */
enum Semester: string
{
    /**
     * Zimní semestr
     */
    case WINTER = 'W';
    /**
     * Letní semestr
     */
    case SUMMER = 'S';

    /**
     * Metoda pro navrácení překladového textu reprezentující daný semestr.
     *
     * @return string překladový text
     */
    public function getName(): string
    {
        return match ($this) {
            self::WINTER => 'Zimní',
            self::SUMMER => 'Letní',
        };
    }
}
