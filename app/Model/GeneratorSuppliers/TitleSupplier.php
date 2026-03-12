<?php

namespace App\Model\GeneratorSuppliers;

/**
 * Třída pro poskytování náhodných nadpisů.
 *
 * @author Michal Turek
 */
class TitleSupplier
{
    /**
     * Nadpisy načtené ze souboru při prvním náhodném výběru.
     *
     * @var string[]
     */
    private array $titles;

    public function __construct(private readonly int $profileId)
    {
    }

    /**
     * Vrátí náhodný nadpis
     *
     * @return string nadpis
     */
    public function getTitle(): string
    {
        if (!isset($this->titles)) {
            if (file_exists(DOCUMENT_FOLDER . '/texts/' . $this->profileId . '/title.txt')) {
                $this->titles = array_filter(file(DOCUMENT_FOLDER . '/texts/' . $this->profileId . '/title.txt', FILE_IGNORE_NEW_LINES));
            } else {
                $this->titles = array_filter(file(ROOT_DIR . '/texts/title.txt', FILE_IGNORE_NEW_LINES));
            }
        }

        return $this->titles[array_rand($this->titles)];
    }
}