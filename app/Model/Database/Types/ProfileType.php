<?php

declare(strict_types=1);

namespace App\Model\Database\Types;

/**
 * Typ generátoru pro profil zadání
 *
 * @author Michal Turek
 */
enum ProfileType: string
{
    /**
     * Textový procesor
     */
    case DOCUMENT = 'document';
    /**
     * Tabulkový procesor
     */
    case TABLE_PROCESSOR = 'table_processor';

    /**
     * Metoda pro navrácení překladového textu reprezentující daný typ generátoru.
     *
     * @return string překladový text
     */
    public function getName(): string
    {
        return match ($this) {
            self::DOCUMENT => 'Dokument',
            self::TABLE_PROCESSOR => 'Tabulkový procesor',
        };
    }
}
