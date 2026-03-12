<?php

namespace App\Generator\TextDocument;

use PhpOffice\PhpWord\Element\Section;

/**
 * Třída představující číslovaný nebo nečíslovaný dvouúrovňový seznam.
 *
 * @author Michal Turek
 */
readonly class PointList implements BodyContent
{
    /**
     * @param bool $ordered true, pokud se jedná o číslovaný seznam
     * @param array<string, string[]> $data položky seznamu
     */
    public function __construct(
        public bool $ordered,
        public array $data,
    ) {
    }

    public function getSourceLines(): array
    {
        $lines = [];

        foreach ($this->data as $key => $secondLevel) {
            $lines[] = $key;
            foreach ($secondLevel as $secondLevelItem) {
                $lines[] = $secondLevelItem;
            }
        }

        return $lines;
    }

    public function insertToSection(Section $section): void
    {
        foreach ($this->data as $key => $secondLevel) {
            $section->addListItem($key, 0);
            foreach ($secondLevel as $secondLevelItem) {
                $section->addListItem($secondLevelItem, 1);
            }
        }
    }
}