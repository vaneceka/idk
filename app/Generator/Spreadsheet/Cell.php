<?php

namespace App\Generator\Spreadsheet;

/**
 * Třída popisující obsah jedné buňky v dokumentu.
 *
 * @author Michal Turek
 */
readonly class Cell
{
    /**
     * @param string|int|float|null $value hodnota buňky nebo null
     * @param string|null $expression výraz, který má student použít v buňce, nebo null
     * @param string|null $numberFormat formát čísla v buňce nebo null
     * @param bool $bold true, pokud má být text v buňce tučný
     * @param bool $alignment true, pokud má být text zarovnán na střed (horizontálně i vertikálně)
     * @param ConditionalFormat[] $conditionalFormat podmíněná formátování pro danou buňku
     */
    public function __construct(
        public string|int|float|null $value = null,
        public ?string $expression = null,
        public ?string $numberFormat = null,
        public bool $bold = false,
        public bool $alignment = false,
        public array $conditionalFormat = [],
    ) {
    }
}