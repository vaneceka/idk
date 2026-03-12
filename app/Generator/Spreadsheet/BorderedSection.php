<?php

namespace App\Generator\Spreadsheet;

/**
 * Třída popisující oblast dokumentu s vnějším a vnitřním ohraničením.
 *
 * @author Michal Turek
 */
readonly class BorderedSection
{
    /**
     * @param string $location oblast v dokumentu
     * @param string $outlineBorderStyle styl vnějšího rámečku
     * @param string $insideBorderStyle styl vnitřního rámečku
     */
    public function __construct(
        public string $location,
        public string $outlineBorderStyle,
        public string $insideBorderStyle,
    ) {
    }
}