<?php

namespace App\Generator\Spreadsheet;

/**
 * Rozhraní představující generátor zadání pro tabulkový procesor.
 *
 * @author Michal Turek
 */
interface SpreadsheetGenerator
{
    /**
     * Vygeneruje nové zadání.
     *
     * @param string $identifier identifikátor dokumentu
     * @param int $minRows minimální počet řádek dat
     * @param int $maxRows maximální počet řádek dat
     * @return Spreadsheet objekt popisující vygenerovaný dokument
     */
    public function generate(string $identifier, int $minRows, int $maxRows): Spreadsheet;
}