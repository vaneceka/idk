<?php

namespace App\Generator\TextDocument;

use PhpOffice\PhpWord\Element\Section;
use PhpOffice\PhpWord\IOFactory;
use PhpOffice\PhpWord\PhpWord;
use PhpOffice\PhpWord\Settings;
use PhpOffice\PhpWord\SimpleType\Jc;
use PhpOffice\PhpWord\Style\Tab;

/**
 * Třída představující vygenerovaný textový dokument.
 *
 * @author Michal Turek
 */
class TextDocument
{
    /**
     * Téma textu
     *
     * @var string
     */
    public string $topic;
    /**
     * Jméno a příjmení studenta
     *
     * @var string
     */
    public string $name;
    /**
     * Identifikátor zadání
     *
     * @var string
     */
    public string $identifier;
    /**
     * Části dokumentu v hlavním oddílu
     *
     * @var TextDocumentPart[]
     */
    public array $parts = [];
    /**
     * Objekty obrázků, které mají být vloženy na libovolné místo v dokumentu
     *
     * @var ImageObject[]
     */
    public array $objects = [];
    /**
     * Seznam literatury
     *
     * @var array{type: string, data: array<string|int, mixed>}[]
     */
    public array $bibliography = [];

    /**
     * Vytvoří soubor zadání.
     *
     * @param string $filename jméno výstupního souboru
     * @param string $fileFormat formát souboru (Word2007, ODText apod.)
     */
    public function createSourceFile(string $filename, string $fileFormat = 'Word2007'): void
    {
        $doc = new PhpWord();
        $doc->getDocInfo()->setCustomProperty('IndividualWorkKey', $this->identifier);

        $section = $doc->addSection();

        $this->fillParts($section, $this->parts);

        $writer = IOFactory::createWriter($doc, $fileFormat);
        $writer->save($filename);
    }

    /**
     * Naplní oddíl dokumentu danými částmi
     *
     * @param Section oddíl dokumentu
     * @param TextDocumentPart[] $parts části dokumentu
     */
    private function fillParts(Section $section, array $parts): void
    {
        foreach ($parts as $part) {
            $section->addText($part->name);
            foreach ($part->content as $content) {
                foreach ($content->getSourceLines() as $sourceLine) {
                    $section->addText($sourceLine);
                }
            }
            if ($part->subparts) {
                $this->fillParts($section, $part->subparts);
            }
        }
    }

    /**
     * Vytvoří strojově čitelný popis zadání ve formátu JSON.
     *
     * @return string JSON obsahující popis zadání
     */
    public function createJsonDescription(): string
    {
        $data = [
            'styles' => [
                'desky-fakulta' => [
                    'type' => 'Times New Roman',
                    'size' => 18,
                    'bold' => true,
                    'allCaps' => true,
                    'alignment' => Jc::CENTER,
                ],
                'desky-nazev-prace' => [
                    'type' => 'Times New Roman',
                    'basedOn' => 'desky-fakulta',
                    'size' => 36,
                    'bold' => true,
                    'allCaps' => true,
                    'alignment' => Jc::CENTER,
                    'spaceBefore' => 200 * 20,
                ],
                'desky-rok-a-jmeno' => [
                    'type' => 'Times New Roman',
                    'size' => 14,
                    'bold' => true,
                    'spaceBefore' => 300 * 20,
                    'tabs' => [
                        ['left', 1133], // approx. 2cm
                        ['right', 7936], // approx. 14cm
                    ],
                ],
                'uvodni-tema' => [
                    'type' => 'Times New Roman',
                    'basedOn' => 'desky-fakulta',
                    'size' => 26,
                    'bold' => true,
                    'alignment' => Jc::CENTER,
                    'spaceBefore' => 200 * 20,
                ],
                'uvodni-autor' => [
                    'type' => 'Times New Roman',
                    'alignment' => Jc::CENTER,
                    'spaceBefore' => 30 * 20,
                    'size' => 20,
                    'italic' => true,
                ],
                'Normal' => [
                    'type' => 'Times New Roman',
                    'size' => 12,
                    'alignment' => Jc::BOTH,
                    'lineHeight' => 1.5,
                ],
                'Heading 1' => [
                    'type' => 'Times New Roman',
                    'size' => 16,
                    'bold' => true,
                    'allCaps' => true,
                    'pageBreakBefore' => true,
                    'numLevel' => 0,
                    'alignment' => Jc::START,
                    'color' => '000000',
                ],
                'Heading 2' => [
                    'type' => 'Times New Roman',
                    'size' => 14,
                    'bold' => true,
                    'numLevel' => 1,
                    'alignment' => Jc::START,
                    'color' => '000000',
                ],
                'Heading 3' => [
                    'type' => 'Times New Roman',
                    'size' => 12,
                    'bold' => true,
                    'numLevel' => 2,
                    'alignment' => Jc::START,
                    'color' => '000000',
                ],
                'Content Heading' => [
                    'type' => 'Times New Roman',
                    'size' => 16,
                    'bold' => true,
                    'alignment' => Jc::START,
                    'color' => '000000',
                ],
                'Caption' => [
                    'italic' => true,
                    'alignment' => Jc::START,
                    'color' => '000000',
                ],
                'Bibliography' => [
                    'alignment' => Jc::START,
                ],
            ],
            'headlines' => [],
            'objects' => [],
            'bibliography' => $this->bibliography,
        ];

        $headlineFill = function (array $parts, int $level) use (&$data, &$headlineFill) {
            foreach ($parts as $part) {
                $data['headlines'][] = [
                    'text' => $part->name,
                    'level' => $level,
                ];
                $headlineFill($part->subparts, $level + 1);
            }
        };

        $headlineFill($this->parts, 1);

        foreach ($this->objects as $object) {
            $data['objects'][] = [
                'type' => 'image',
                'caption' => $object->caption,
                'data' => $object->identifier, // data in QR code
            ];
        }

        return json_encode($data, JSON_PRETTY_PRINT);
    }

    /**
     * Vytvoří textový popis zadání pro studenty.
     *
     * @return string popis zadání
     */
    public function createAssignmentDescription(): string
    {
        $year = date('Y');
        $text = "Samostatná práce 1
==================

1) Otevřete soubor $this->identifier.docx v Microsoft Word nebo $this->identifier.odt v LibreOffice Writer. Uvnitř souboru najdete neformátovaný text, se kterým budete pracovat. Veškerý postup ukládejte do tohoto souboru a tento soubor také odevzdejte. Nové soubory nevytvářejte!
2) Rozdělte dokument na tři oddíly. Text, jenž se v dokumentu již vyskytuje, tvoří druhý oddíl.
3) První oddíl bude mít záhlaví i zápatí prázdné. Prvním listem budou desky práce, následně úvodní list a obsah.
4) Pro první list dokumentu, tedy desky práce, vytvořte tři vlastní styly, které postupně použijete:
    a) desky-fakulta: 18px, tučně, na střed a všechna písmena velká pro text „Fakulta zdravotnických studií“
    b) desky-nazev-prace: založen na stylu desky-fakulta, 36 px a mezera před odstavcem 200 b. pro text „Semestrální práce 1“
    c) desky-rok-a-jmeno: 14 px, tučně, mezera před odstavcem 300 b., tabulátor na 2 cm se zarovnáním textu vlevo a na 14 cm se zarovnáním textu vpravo. Rok „{$year}“ bude umístěn na první tabulátor a vaše jméno bude na druhém tabulátoru.
5) Pro druhý list dokumentu, tedy úvodní list, vytvořte či použijte vlastní styly.
    a) znovu použijte styl desky-fakulta pro text „Fakulta zdravotnických studií“.
    b) uvodni-tema: 26 px, tučně, na střed a mezera před odstavcem 200 b. pro text „{$this->topic}“
    c) uvodni-autor: 20px, kurzíva, na střed a mezera před odstavcem 30 b., který použijete pro vaše jméno a příjmení.
6) V záhlaví druhého oddílu bude vlevo text „{$this->topic}“ a vpravo vaše jméno a příjmení.
7) V zápatí bude číslo stránky začínající od 1, umístěné uprostřed.
4) Změňte styly, které použijete pro druhý oddíl dokumentu.
    a) Normální: písmo Times New Roman, 12 px, zarovnání do bloku, nastaveno 1,5násobné řádkování
    b) Nadpis 1: písmo Times New Roman, 16 px, tučně, zarovnání vlevo, černé písmo, velká písmena, vložit konec stránky před, aktivní víceúrovňové číslování
    c) Nadpis 2: písmo Times New Roman, 14 px, tučně, zarovnání vlevo, černé písmo, aktivní víceúrovňové číslování
    d) Nadpis 3: písmo Times New Roman, 12 px, tučně, zarovnání vlevo, černé písmo, aktivní víceúrovňové číslování
    e) Nadpis obsahu: písmo Times New Roman, 16 px, tučně, zarovnání vlevo, černé písmo
    f) Titulek: kurzíva, černá barva, zarovnání vlevo
    g) Bibliografie: zarovnání vlevo
5) Vhodně použijte styly v druhém oddílu dokumentu. Struktura nadpisů je následující:
";

        $headlineFill = function (array $parts, int $level) use (&$text, &$headlineFill) {
            foreach ($parts as $part) {
                $text .= str_repeat('  ', $level) . '- ' . $part->name . "\r\n";
                $headlineFill($part->subparts, $level + 1);
            }
        };

        $headlineFill($this->parts, 0);

        $pictureStr = join("\r\n", array_map(
            fn(ImageObject $image): string => '       - ' . $image->identifier . '.png - „' . $image->caption . '“',
            $this->objects,
        ));

        $bibString = join("\r\n", array_map(
            fn(array $bib): string => '       - ' . $this->formatReference($bib),
            $this->bibliography,
        ));

        $text .= "6) Bez jakýchkoli úprav použijte následující styly:
    a) Číslovaný seznam: použijte jako hlavní úroveň seznamu, pokud budete mít položky na jejichž pořadí záleží.
    b) Číslovaný seznam 2: použijete jako druhou úroveň seznamu, pokud budete mít položky na jejichž pořadí záleží.
    c) Seznam s odrážkami: použijete jako hlavní úroveň seznamu, pokud nezáleží na pořadí položek.
    d) Seznam s odrážkami 2: použijete jako druhou úroveň seznamu, pokud nezáleží na pořadí položek.
7) Do dokumentu vložte na vhodná místa obrázky, které jsou součástí zadání. Řiďte se přitom následujícími pravidly:
    a) Obrázek přes celou šířku stránky nesmí přesahovat třetinu výšky stránky.
    b) Pro větší/vyšší obrázky nastavte jeho šířku na 7 cm, obtékání/zalamování textu a přesuňte jej k pravému okraji.
    c) K vloženému objektu přidejte titulky. Objekt s titulkem spojte do skupiny, aby drželi pohromadě.
    d) Seznam obrázků:
$pictureStr
8) Vložte automaticky generované seznamy pro obsah, grafy, obrázky, tabulky apod.
9) Vytvořte seznam literatury a citace.
    a) Ve správci pramenů vytvořte položky pro všechny prameny dle ISO 690. 
$bibString
    b) Vytvořte číslovaný seznam literatury.
    c) Do dokumentu vhodně vložte citace VŠECH pramenů.
10) Zkontrolujte úplnost dokumentu a aktuálnost všech seznamů.
11) Dokument uložte a zavřete.";
        return $text;
    }

    /**
     * Naformátuje položku v seznamu literatury pro účely zadání.
     *
     * @param array{type: string, data: array<string|int, mixed>} $reference položka seznamu literatury
     * @return string čitelný text představující položku seznamu
     */
    private function formatReference(array $reference): string
    {
        $data = $reference['data'];

        return match ($reference['type']) {
            'book' => "{$data['author']}. {$data['title']}. {$data['address']}: {$data['publisher']}, {$data['year']}. ISBN {$data['isbn']}.",
            'article' => "{$data['author']}. {$data['title']}. {$data['journal']}, {$data['year']}, roč. {$data['volume']}, č. {$data['number']}, s. {$data['pages']}. ISSN {$data['issn']}.",
            'online' => "{$data['author']}. {$data['title']} [online]. {$data['year']}. Dostupné z: {$data['url']}. {$data['note']}.",
            default => '',
        };
    }

    /**
     * Vytvoří soubor náhledu.
     *
     * @param string $filename jméno výstupního souboru
     */
    public function createResultFile(string $filename): void
    {
        $doc = new PhpWord();
        $doc->setDefaultFontName('Times New Roman');
        $doc->setDefaultFontSize(12);
        $doc->setDefaultParagraphStyle([
            'alignment' => Jc::BOTH,
            'lineHeight' => 1.5,
        ]);

        // Názvy stylů oproti Wordu úplně nesedí, což ale nevadí, protože výsledný soubor je PDF.

        $doc->addParagraphStyle('P-desky-fakulta', [
            'alignment' => Jc::CENTER,
        ]);

        $doc->addFontStyle('F-desky-fakulta', [
            'size' => 18,
            'bold' => true,
            'allCaps' => true,
        ]);

        $doc->addParagraphStyle('P-desky-nazev-prace', [
            'basedOn' => 'desky-fakulta',
            'alignment' => Jc::CENTER,

            'spaceBefore' => 200 * 20,
        ]);

        $doc->addFontStyle('F-desky-nazev-prace', [
            'basedOn' => 'desky-fakulta',
            'bold' => true,
            'allCaps' => true,

            'size' => 36,
        ]);

        $doc->addParagraphStyle('P-desky-rok-a-jmeno', [
            'spaceBefore' => 300 * 20,
            'tabs' => [
                new Tab('left', 1133), // approx. 2cm
                new Tab('right', 7936), // approx. 14cm
            ],
        ]);

        $doc->addFontStyle('F-desky-rok-a-jmeno', [
            'size' => 14,
            'bold' => true,
        ]);

        $doc->addParagraphStyle('P-uvodni-tema', [
            'alignment' => Jc::CENTER,
            'spaceBefore' => 200 * 20,
        ]);

        $doc->addFontStyle('F-uvodni-tema', [
            'basedOn' => 'desky-fakulta',
            'size' => 26,
            'bold' => true,
        ]);

        $doc->addParagraphStyle('P-uvodni-autor', [
            'alignment' => Jc::CENTER,
            'spaceBefore' => 30 * 20,
        ]);

        $doc->addFontStyle('F-uvodni-autor', [
            'basedOn' => 'desky-fakulta',
            'size' => 20,
            'italic' => true,
        ]);

        // titles
        // Nefunguje s PDF writerem
//        $doc->addNumberingStyle('hNum', [
//            'type' => 'multilevel',
//            'levels' => [
//                ['pStyle' => 'Heading_1', 'format' => 'decimal', 'text' => '%1'],
//                ['pStyle' => 'Heading_2', 'format' => 'decimal', 'text' => '%1.%2'],
//                ['pStyle' => 'Heading_3', 'format' => 'decimal', 'text' => '%1.%2.%3'],
//            ],
//        ]);

        $doc->addTitleStyle(1, [
            'size' => 16,
            'bold' => true,
            'allCaps' => true,
        ], [
//            'numStyle' => 'hNum',
            'numLevel' => 0,
            'alignment' => Jc::START,
            'pageBreakBefore' => true,
        ]);

        $doc->addTitleStyle(2, [
            'size' => 14,
            'bold' => true,
        ], [
//            'numStyle' => 'hNum',
            'numLevel' => 1,
            'alignment' => Jc::START,
        ]);

        $doc->addTitleStyle(3, [
            'size' => 12,
            'bold' => true,
        ], [
//            'numStyle' => 'hNum',
            'numLevel' => 2,
            'alignment' => Jc::START,
        ]);

        $doc->addFontStyle('P-heading-content', [
            'alignment' => Jc::START,
        ]);

        $doc->addFontStyle('F-heading-contents', [
            'size' => 16,
            'bold' => true,
        ]);

        $doc->addFontStyle('P-caption', [
            'alignment' => Jc::START,
        ]);

        $doc->addFontStyle('F-caption', [
            'italic' => true,
        ]);

        $firstSection = $doc->addSection();
        $firstSection->addText('Fakulta zdravotnických studií', 'F-desky-fakulta', 'P-desky-fakulta');
        $firstSection->addText('Semestrální práce 1', 'F-desky-nazev-prace', 'P-desky-nazev-prace');
        $firstSection->addText(date('Y') . "\t" . $this->name, 'F-desky-rok-a-jmeno', 'P-desky-rok-a-jmeno');
        $firstSection->addPageBreak();
        $firstSection->addText('Fakulta zdravotnických studií', 'F-desky-fakulta', 'P-desky-fakulta');
        $firstSection->addText($this->topic, 'F-uvodni-tema', 'P-uvodni-tema');
        $firstSection->addText($this->name, 'F-uvodni-autor', 'P-uvodni-autor');
        $firstSection->addPageBreak();
        $firstSection->addText('Obsah', 'F-heading-contents', 'P-heading-contents');
        $firstSection->addText('Zde vložte vygenerovaný obsah');

        $secondSection = $doc->addSection();
        $secondSection->addPreserveText('{PAGE}');
        $this->fillPartsResult($secondSection, $this->parts);

        $thirdSection = $doc->addSection();
        $thirdSection->addText('Seznam obrázků', 'F-heading-contents', 'P-heading-contents');
        $thirdSection->addText('Zde vložte generované seznamy objektů');
        $thirdSection->addPageBreak();
        $thirdSection->addText('Seznam literatury', 'F-heading-contents', 'P-heading-contents');
        $thirdSection->addText('Zde vložte seznam literatury');

        Settings::setPdfRendererName(Settings::PDF_RENDERER_MPDF);
        Settings::setPdfRendererPath(__DIR__ . '/../../../vendor/mpdf/mpdf');

        $writer = IOFactory::createWriter($doc, 'PDF');
        $writer->setTempDir(TEMP_DIR . '/mpdf');
        $writer->save($filename);
    }

    /**
     * Naplní oddíl náhledového dokumentu danými částmi v dané úrovni.
     *
     * @param Section oddíl dokumentu
     * @param TextDocumentPart[] $parts části dokumentu
     * @param int $depth úroveň nadpisů
     * @param string|null $numbering řetězec obsahující číslo aktuální kapitoly
     */
    private function fillPartsResult(Section $section, array $parts, int $depth = 1, ?string $numbering = null): void
    {
        $i = 1;
        foreach ($parts as $part) {
            $inHeading = ($numbering !== null ? $numbering . '.' : '') . $i;
            $section->addTitle($inHeading . "\t" . $part->name, $depth);
            foreach ($part->content as $content) {
                $content->insertToSection($section);
            }
            if ($part->subparts) {
                $this->fillPartsResult($section, $part->subparts, $depth + 1, $inHeading);
            }
            $i++;
        }
    }
}