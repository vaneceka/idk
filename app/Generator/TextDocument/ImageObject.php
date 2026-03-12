<?php

namespace App\Generator\TextDocument;

use PhpOffice\PhpWord\Element\Section;

/**
 * Třída představující objekt obrázku.
 *
 * @author Michal Turek
 */
readonly class ImageObject implements BodyContent
{
    /**
     * @param string $identifier identifikátor obrázku
     * @param string $file dočasný soubor s obrázkem
     * @param string $caption popisek obrázku
     */
    public function __construct(
        public string $identifier,
        public string $file,
        public string $caption,
    ) {
    }

    public function __destruct()
    {
        // po zpracování dokumentu dojde ke smazání dočasného souboru
        @unlink($this->file);
    }

    public function getSourceLines(): array
    {
        return []; // do zdroje nedáváme, pouze pro náhled
    }

    public function insertToSection(Section $section): void
    {
        $section->addImage($this->file, [
            'width' => 400,
            'height' => 300,
//            'marginLeft' => 1.13735789,
            'wrappingStyle' => 'behind',
        ]);
        $section->addText('Obrázek X: ' . $this->caption, 'F-caption', 'P-caption');
    }
}