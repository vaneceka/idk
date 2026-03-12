<?php

namespace App\Generator\Spreadsheet;

/**
 * Třída popisující podmíněné formátování jedné buňky.
 *
 * @author Michal Turek
 */
readonly class ConditionalFormat
{
    /**
     * @param string $type typ podmíněného formátování
     * @param string $operator operátor porovnání hodnot
     * @param string|int|float $value statická hodnota, se kterou se hodnota v buňce porovnává
     * @param string|null $fillColor barva výplně buňky, která se má za dané podmínky použít, nebo null
     * @param string|null $textColor barva textu, která se má za dané podmínky použít, nebo null
     */
    public function __construct(
        public string $type,
        public string $operator,
        public string|int|float $value,
        public ?string $fillColor = null,
        public ?string $textColor = null,
    ) {
    }
}