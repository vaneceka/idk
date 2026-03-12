<?php

declare(strict_types=1);

namespace App\Model\Database\Types;

/**
 * Výčet reprezentující typ souboru.
 *
 * @author Michal Turek
 */
enum FileType: int
{
    /**
     * Vygenerovaný soubor s popisem zadání
     */
    case ASSIGNMENT_TXT = 0;
    /**
     * Vygenerovaný soubor se strojově čitelným JSOM popisem zadání
     */
    case ASSIGNMENT_JSON = 1;
    /**
     * Vstupní soubor zadání (textový dokument, tabulka, obrázek)
     */
    case INPUT = 2;
    /**
     * Soubor s náhledem výsledku
     */
    case PREVIEW = 3;
    /**
     * Soubor se studentovým odevzdáním.
     */
    case UPLOAD = 4;

    /**
     * Metoda pro navrácení překladového textu reprezentující daný typ souboru.
     *
     * @return string překladový text
     */
    public function getName(): string
    {
        return match ($this) {
            self::ASSIGNMENT_TXT => 'Text zadání',
            self::ASSIGNMENT_JSON => 'Strojový JSON popis',
            self::INPUT => 'Soubor zadání',
            self::PREVIEW => 'Soubor náhledu',
            self::UPLOAD => 'Odevzdané vypracování',
        };
    }
}
