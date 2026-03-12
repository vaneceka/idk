<?php

namespace App\Generator\Spreadsheet;

/**
 * Třída popisující graf v dokumentu.
 *
 * @author Michal Turek
 */
readonly class Graph
{
    /**
     * @param string $title název grafu
     * @param string $type typ grafu
     * @param array<string, string> $categories pole oblastí kategorií (oblast kategorie => popisek kategorie)
     * @param array<string, string> $values pole oblastí hodnot (oblast hodnot => popisek hodnot)
     * @param string $description zadání pro studenty popisující vytvářený graf
     * @param string $xAxisLabel popisek osy X
     * @param string $yAxisLabel popisek osy Y
     */
    public function __construct(
        public string $title,
        public string $type,
        public array $categories,
        public array $values,
        public string $description,
        public string $xAxisLabel,
        public string $yAxisLabel,
    ) {
    }
}