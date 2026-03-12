<?php

namespace App\Model\GeneratorSuppliers;

/**
 * Třída pro poskytování náhodných popisků obrázků.
 *
 * @author Michal Turek
 */
class CaptionSupplier
{
    /**
     * Popisky obrázků načtené ze souboru při prvním náhodném výběru.
     *
     * @var string[]
     */
    private array $captions;

    public function __construct(private readonly int $profileId)
    {
    }

    /**
     * Vrátí náhodný popisek obrázku
     *
     * @return string náhodný popisek
     */
    public function getCaption(): string
    {
        if (!isset($this->captions)) {
            if (file_exists(DOCUMENT_FOLDER . '/texts/' . $this->profileId . '/caption.txt')) {
                $this->captions = array_filter(file(DOCUMENT_FOLDER . '/texts/' . $this->profileId . '/caption.txt', FILE_IGNORE_NEW_LINES));
            } else {
                $this->captions = array_filter(file(ROOT_DIR . '/texts/caption.txt', FILE_IGNORE_NEW_LINES));
            }
        }

        return $this->captions[array_rand($this->captions)];
    }
}