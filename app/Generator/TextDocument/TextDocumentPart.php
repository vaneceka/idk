<?php

namespace App\Generator\TextDocument;

/**
 * Třída představující část dokumentu v hlavním oddílu.
 *
 * @author Michal Turek
 */
class TextDocumentPart
{
    /**
     * Nadpis
     *
     * @var string
     */
    public string $name;
    /**
     * Obsah v dané části
     *
     * @var BodyContent[]
     */
    public array $content = [];
    /**
     * Podčásti/podkapitoly
     *
     * @var TextDocumentPart[]
     */
    public array $subparts = [];
}