<?php

namespace App\Generator\TextDocument;

use PhpOffice\PhpWord\Element\Section;

/**
 * Třída představující jeden odstavec.
 *
 * @author Michal Turek
 */
readonly class Paragraph implements BodyContent
{
    /**
     * @param string $content text odstavce
     */
    public function __construct(
        public string $content,
    ) {
    }

    public function getSourceLines(): array
    {
        return [$this->content];
    }

    public function insertToSection(Section $section): void
    {
        $section->addText($this->content);
    }
}