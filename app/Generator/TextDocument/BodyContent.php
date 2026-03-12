<?php

namespace App\Generator\TextDocument;

use PhpOffice\PhpWord\Element\Section;

/**
 * Rozhraní reprezentující libovolný objekt uvnitř druhého oddílu dokumentu
 *
 * @author Michal Turek
 */
interface BodyContent
{
    /**
     * Vrátí řádky pro zdrojový neformátovaný soubor
     *
     * @return string[]
     */
    public function getSourceLines(): array;

    /**
     * Vloží objekt do náhledového dokumentu
     *
     * @param Section $section sekce, do které bude objekt vložen
     */
    public function insertToSection(Section $section): void;
}