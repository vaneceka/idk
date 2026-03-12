<?php

namespace App\Model\GeneratorSuppliers;

use App\Generator\TextDocument\Paragraph;

/**
 * Třída pro poskytování náhodných odstavců.
 *
 * @author Michal Turek
 */
class ParagraphSupplier
{
    /**
     * Věty načtené ze souboru při generování prvního odstavce.
     *
     * @var string[]
     */
    private array $sentences;

    public function __construct(private readonly int $profileId)
    {
    }

    /**
     * Vrátí náhodný odstavec
     *
     * @return Paragraph náhodný odstavec
     */
    public function getParagraph(): Paragraph
    {
        if (!isset($this->sentences)) {
            if (file_exists(DOCUMENT_FOLDER . '/texts/' . $this->profileId . '/sentences.txt')) {
                $this->sentences = array_filter(file(DOCUMENT_FOLDER . '/texts/' . $this->profileId . '/sentences.txt', FILE_IGNORE_NEW_LINES));
            } else {
                $this->sentences = array_filter(file(ROOT_DIR . '/texts/sentences.txt', FILE_IGNORE_NEW_LINES));
            }
        }

        $par = '';
        for ($i = 0; $i < rand(4, 5); $i++) {
            $par .= $this->sentences[array_rand($this->sentences)] . ' ';
        }
        return new Paragraph(trim($par));
    }
}