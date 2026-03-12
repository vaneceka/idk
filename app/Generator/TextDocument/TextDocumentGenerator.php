<?php

namespace App\Generator\TextDocument;

use App\Model\GeneratorSuppliers\BibliographySupplier;
use App\Model\GeneratorSuppliers\CaptionSupplier;
use App\Model\GeneratorSuppliers\ListSupplier;
use App\Model\GeneratorSuppliers\ParagraphSupplier;
use App\Model\GeneratorSuppliers\TitleSupplier;
use App\Model\GeneratorSuppliers\TopicSupplier;
use chillerlan\QRCode\QRCode;
use chillerlan\QRCode\QROptions;
use Imagine\Gd\Imagine;
use Imagine\Image\Box;
use Imagine\Image\Palette\RGB;
use Imagine\Image\Point;

/**
 * Generátor zadání textového procesoru.
 *
 * @author Michal Turek
 */
class TextDocumentGenerator
{
    private int $introParagraphsFrom;
    private int $introParagraphsTo;
    private int $section1From;
    private int $section1To;
    private int $section1ParagraphsFrom;
    private int $section1ParagraphsTo;
    private int $section2From;
    private int $section2To;
    private int $section2ParagraphsFrom;
    private int $section2ParagraphsTo;
    private int $section3From;
    private int $section3To;
    private int $section3ParagraphsFrom;
    private int $section3ParagraphsTo;
    private int $conclusionParagraphsFrom;
    private int $conclusionParagraphsTo;
    private int $bibliographyFrom;
    private int $bibliographyTo;

    private ParagraphSupplier $paragraphSupplier;
    private TopicSupplier $topicSupplier;
    private TitleSupplier $titleSupplier;
    private CaptionSupplier $captionSupplier;
    private ListSupplier $listSupplier;
    private BibliographySupplier $bibliographySupplier;

    /**
     * @param int $profileId ID profilu zadání
     */
    public function __construct(private readonly int $profileId)
    {
        $this->paragraphSupplier = new ParagraphSupplier($this->profileId);
        $this->topicSupplier = new TopicSupplier($this->profileId);
        $this->titleSupplier = new TitleSupplier($this->profileId);
        $this->captionSupplier = new CaptionSupplier($this->profileId);
        $this->listSupplier = new ListSupplier($this->profileId);
        $this->bibliographySupplier = new BibliographySupplier($this->profileId);
    }

    /**
     * Načte předané nastavení generátoru.
     *
     * @param array $options nastavení generátoru
     */
    public function loadOptions(array $options): void
    {
        $this->introParagraphsFrom = (int) ($options['intro_paragraphs_from'] ?? 1);
        $this->introParagraphsTo = (int) ($options['intro_paragraphs_to'] ?? 2);
        $this->section1From = (int) ($options['section_1_from'] ?? 2);
        $this->section1To = (int) ($options['section_1_to'] ?? 3);
        $this->section1ParagraphsFrom = (int) ($options['section_1_paragraphs_from'] ?? 1);
        $this->section1ParagraphsTo = (int) ($options['section_1_paragraphs_to'] ?? 1);
        $this->section2From = (int) ($options['section_2_from'] ?? 2);
        $this->section2To = (int) ($options['section_2_to'] ?? 3);
        $this->section2ParagraphsFrom = (int) ($options['section_2_paragraphs_from'] ?? 2);
        $this->section2ParagraphsTo = (int) ($options['section_2_paragraphs_to'] ?? 3);
        $this->section3From = (int) ($options['section_3_from'] ?? 2);
        $this->section3To = (int) ($options['section_3_to'] ?? 4);
        $this->section3ParagraphsFrom = (int) ($options['section_3_paragraphs_from'] ?? 2);
        $this->section3ParagraphsTo = (int) ($options['section_3_paragraphs_to'] ?? 3);
        $this->conclusionParagraphsFrom = (int) ($options['conclusion_paragraphs_from'] ?? 1);
        $this->conclusionParagraphsTo = (int) ($options['conclusion_paragraphs_to'] ?? 2);
        $this->bibliographyFrom = (int) ($options['bibliography_from'] ?? 3);
        $this->bibliographyTo = (int) ($options['bibliography_to'] ?? 3);
    }

    /**
     * Vygeneruje textový dokument.
     *
     * @param string $name jméno a příjmení studenta
     * @param string $studentNumber osobní číslo
     * @return TextDocument objekt představující vygenerovaný textový dokument
     */
    public function generate(string $name, string $studentNumber): TextDocument
    {
        $document = new TextDocument();
        $document->topic = $this->topicSupplier->getTitle();
        $document->identifier = $studentNumber . '_' . substr(md5(microtime()), rand(0, 26), 5);
        $document->name = $name;

        $document->objects[] = $image1 = $this->generateImage($document->identifier . '_01');
        $document->objects[] = $image2 = $this->generateImage($document->identifier . '_02');

        $hasOrderedList = false;
        $hasUnorderedList = false;

        // Intro
        $intro = new TextDocumentPart();
        $intro->name = 'Úvod';
        $this->generateParagraphs($intro, $this->introParagraphsFrom, $this->introParagraphsTo);
        $document->parts[] = $intro;

        // Body
        $bodyParts = rand($this->section1From, $this->section1To);
        for ($i = 0; $i < $bodyParts; $i++) {
            $part = new TextDocumentPart();
            $part->name = $this->titleSupplier->getTitle();
            $this->generateParagraphs($part, $this->section1ParagraphsFrom, $this->section1ParagraphsTo);
            $document->parts[] = $part;

            if ($image1 !== null) {
                $part->content[] = $image1;
                $image1 = null;
            } else if ($image2 !== null) {
                $part->content[] = $image2;
                $image2 = null;
            }

            $subparts = rand($this->section2From, $this->section2To);
            for ($j = 0; $j < $subparts; $j++) {
                $innerPart = new TextDocumentPart();
                $innerPart->name = $this->titleSupplier->getTitle();
                if (rand(0, 1) === 1) {
                    $level3Parts = rand($this->section3From, $this->section3To);
                    for ($k = 0; $k < $level3Parts; $k++) {
                        $level3Part = new TextDocumentPart();
                        $level3Part->name = $this->titleSupplier->getTitle();
                        $this->generateParagraphs($level3Part, $this->section3ParagraphsFrom, $this->section3ParagraphsTo);
                        $innerPart->subparts[] = $level3Part;
                        if (rand(0, 1) === 1) {
                            if (!$hasOrderedList) {
                                $level3Part->content[] = $this->listSupplier->getList(true);
                                $hasOrderedList = true;
                            } else if (!$hasUnorderedList) {
                                $level3Part->content[] = $this->listSupplier->getList(false);
                                $hasUnorderedList = true;
                            }
                        }
                    }
                } else {
                    $this->generateParagraphs($innerPart, $this->section2ParagraphsFrom, $this->section2ParagraphsTo);
                }
                $part->subparts[] = $innerPart;
            }
        }

        // Summary
        $summary = new TextDocumentPart();
        $summary->name = 'Závěr';
        $this->generateParagraphs($summary, $this->conclusionParagraphsFrom, $this->conclusionParagraphsTo);
        $document->parts[] = $summary;

        $document->bibliography = $this->bibliographySupplier->getSources(rand($this->bibliographyFrom, $this->bibliographyTo));

        return $document;
    }

    /**
     * Vygeneruje náhodný počet odstavců v daném rozmezí
     *
     * @param TextDocumentPart $part část dokumentu, do které budou odstavce vloženy
     * @param int $min minimální počet odstavců
     * @param int $max maximální počet odstavců
     */
    private function generateParagraphs(TextDocumentPart $part, int $min, int $max): void
    {
        $paragraphs = rand($min, $max);
        for ($i = 0; $i < $paragraphs; $i++) {
            $part->content[] = $this->paragraphSupplier->getParagraph();
        }
    }

    /**
     * Vygeneruje náhodný obrázek obsahující QR kód a náhodný útvar v náhodné barvě.
     *
     * @param string $identifier identifikátor obrázku
     * @return ImageObject objekt představující vygenerovaný obrázek
     */
    private function generateImage(string $identifier): ImageObject
    {
        $imagine = new Imagine();
        $rgbPalette = new RGB();

        $width = 400;
        $height = 300;
        $image = $imagine->create(new Box($width, $height), $rgbPalette->color('#FFFFFF'));

        $colors = ['#FF0000', '#00FF00', '#0000FF', '#FF00FF', '#FFFF00', '#00FFFF'];
        $color = $rgbPalette->color($colors[array_rand($colors)]);

        $shapes = ['rectangle', 'circle', 'triangle'];
        $shape = $shapes[array_rand($shapes)];

        if ($shape == 'rectangle') {
            $rectX = rand(0, $width / 2);
            $rectY = rand(0, $height / 2);
            $rectWidth = rand(50, $width - $rectX);
            $rectHeight = rand(50, $height - $rectY);

            $image->draw()
                ->rectangle(
                    new Point($rectX, $rectY),
                    new Point($rectX + $rectWidth, $rectY + $rectHeight),
                    $color,
                    true,
                );
        } elseif ($shape == 'circle') {
            $radius = rand(50, 150);

            $image->draw()->circle(
                new Point(rand(0, $width), rand(0, $height)),
                $radius,
                $color,
                true,
            );
        } elseif ($shape == 'triangle') {
            $image->draw()->polygon(
                [
                    new Point(rand(0, $width), rand(0, $height)),
                    new Point(rand(0, $width), rand(0, $height)),
                    new Point(rand(0, $width), rand(0, $height)),
                ],
                $color,
                true,
            );
        }

        $options = new QROptions([
            'version' => 2,
            'outputType' => 'png',
        ]);
        $code = new QRCode($options);
        $output = $code->render($identifier);

        $overlay = $imagine->load(base64_decode(substr($output, strlen('data:image/png;base64,'))))->resize(new Box(100, 100));

        $position = match (rand(1, 4)) {
            1 => new Point(0,0),
            2 => new Point($width - 100, 0),
            3 => new Point(0, $height - 100),
            4 => new Point($width - 100, $height - 100),
        };
        $image->paste($overlay, $position);

        @mkdir(__DIR__ . '/../../../temp');
        $filename = tempnam(__DIR__ . '/../../../temp', 'ImageObject');
        $image->save($filename, ['format' => 'png']);
        return new ImageObject(
            $identifier,
            $filename,
            $this->captionSupplier->getCaption(),
        );
    }
}