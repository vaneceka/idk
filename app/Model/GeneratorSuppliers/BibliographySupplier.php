<?php

namespace App\Model\GeneratorSuppliers;

/**
 * Třída pro poskytování náhodných zdrojů.
 *
 * @author Michal Turek
 */
class BibliographySupplier
{
    /**
     * Zdroje načtené z json souboru s konkrétní strukturou.
     *
     * @var array{type: string, data: array<string|int, mixed>}[]
     */
    private array $bibliography;

    public function __construct(private readonly int $profileId)
    {
    }

    /**
     * Vrátí X náhodných zdrojů.
     *
     * @return array{type: string, data: array<string|int, mixed>}[]
     */
    public function getSources(int $number): array
    {
        if (!isset($this->bibliography)) {
            if (file_exists(DOCUMENT_FOLDER . '/texts/' . $this->profileId . '/bibliography.json')) {
                $this->bibliography = json_decode(file_get_contents(DOCUMENT_FOLDER . '/texts/' . $this->profileId . '/bibliography.json'), true);
            } else {
                $this->bibliography = json_decode(file_get_contents(ROOT_DIR . '/texts/bibliography.json'), true);
            }
        }

        $keys = array_rand($this->bibliography, $number);
        $result = [];
        foreach ($keys as $key) {
            $result[] = $this->bibliography[$key];
        }
        return $result;
    }
}