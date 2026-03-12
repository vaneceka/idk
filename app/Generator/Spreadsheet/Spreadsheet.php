<?php

namespace App\Generator\Spreadsheet;

use PhpOffice\PhpSpreadsheet\Chart\Chart;
use PhpOffice\PhpSpreadsheet\Chart\DataSeries;
use PhpOffice\PhpSpreadsheet\Chart\DataSeriesValues;
use PhpOffice\PhpSpreadsheet\Chart\Legend;
use PhpOffice\PhpSpreadsheet\Chart\PlotArea;
use PhpOffice\PhpSpreadsheet\Chart\Renderer\MtJpGraphRenderer;
use PhpOffice\PhpSpreadsheet\Chart\Title;
use PhpOffice\PhpSpreadsheet\IOFactory;
use PhpOffice\PhpSpreadsheet\Settings;
use PhpOffice\PhpSpreadsheet\Shared\StringHelper;
use PhpOffice\PhpSpreadsheet\Spreadsheet as PHPOfficeSpreadsheet;
use PhpOffice\PhpSpreadsheet\Style\Alignment;
use PhpOffice\PhpSpreadsheet\Style\Conditional;
use PhpOffice\PhpSpreadsheet\Style\Fill;
use PhpOffice\PhpSpreadsheet\Worksheet\PageSetup;
use PhpOffice\PhpSpreadsheet\Writer\Pdf;

/**
 * Třída popisující vygenerovaný dokument pro tabulkový procesor.
 *
 * @author Michal Turek
 */
class Spreadsheet
{
    /**
     * Identifikátor dokumentu
     *
     * @var string
     */
    public string $identifier;
    /**
     * Pole obsahující vstupní data. Indexem je označení buňky v podobě A1 apod.
     *
     * @var array<string, Cell>
     */
    public array $cells = [];
    /**
     * Oblasti s vnějším nebo vnitřním ohraničením
     *
     * @var BorderedSection[]
     */
    public array $borders = [];
    /**
     * Graf v dokumentu
     *
     * @var Graph
     */
    public Graph $graph;
    /**
     * Popis vzorce, který musí student v jednom ze sloupců vytvořit
     *
     * @var string
     */
    public string $expressionDescription;
    /**
     * Popisy všech podmíněných formátů, které musí student vytvořit
     *
     * @var string[]
     */
    public array $conditionalFormatDescription = [];

    /**
     * Vytvoří soubor zadání nebo náhledu.
     *
     * @param string $filename jméno výstupního souboru
     * @param string $fileFormat formát souboru (Xlsx, Ods, Mpdf apod.)
     * @param bool $result true, pokud se má jednat o náhled, jinak false
     * @return void
     */
    public function createSourceFile(string $filename, string $fileFormat = 'Xlsx', bool $result = false): void
    {
        $doc = new PHPOfficeSpreadsheet();
        $doc->getProperties()->setCustomProperty('IndividualWorkKey', $this->identifier);

        $sheet = $doc->getActiveSheet();
        $sheet->setTitle('data');

        foreach ($this->cells as $cellName => $cell) {
            if ($cell->value !== null) {
                $sheet->getCell($cellName)->setValue($cell->value);
            }
            if ($cell->expression !== null) {
                if ($result) {
                    $sheet->getCell($cellName)->setValue($cell->expression);
                } else {
                    $sheet->getCell($cellName)->getStyle()->applyFromArray([
                        'fill' => [
                            'fillType' => Fill::FILL_SOLID,
                            'startColor' => [
                                'rgb' => 'FFF5CE',
                            ],
                        ],
                    ]);
                }
            }
            if ($result) {
                $style = $sheet->getCell($cellName)->getStyle();
                if ($cell->numberFormat !== null) {
                    $style->getNumberFormat()->setFormatCode($cell->numberFormat);
                }
                $style->getFont()->setBold($cell->bold);
                if ($cell->alignment) {
                    $style->getAlignment()->setVertical(Alignment::VERTICAL_CENTER);
                    $style->getAlignment()->setHorizontal(Alignment::HORIZONTAL_CENTER);
                }
                foreach ($cell->conditionalFormat as $conditionalFormat) {
                    $conditional = new Conditional();
                    $conditional->setConditionType($conditionalFormat->type);
                    $conditional->setOperatorType($conditionalFormat->operator);
                    $conditional->addCondition($conditionalFormat->value);
                    if ($conditionalFormat->textColor !== null) {
                        $conditional->getStyle()->getFont()->getColor()->setRGB($conditionalFormat->textColor);
                    }
                    if ($conditionalFormat->fillColor !== null) {
                        $conditional->getStyle()->applyFromArray([
                            'fill' => [
                                'fillType' => Fill::FILL_SOLID,
                                'startColor' => [
                                    'rgb' => $conditionalFormat->fillColor,
                                ],
                            ],
                        ]);
                    }
                    $conditionalStyles = $style->getConditionalStyles();
                    $conditionalStyles[] = $conditional;

                    $style->setConditionalStyles($conditionalStyles);
                }
            }
            $sheet->getColumnDimension(substr($cellName, 0, 1))->setAutoSize(true);
        }

        if ($result) {
            foreach ($this->borders as $border) {
                $sheet->getStyle($border->location)->applyFromArray([
                    'borders' => [
                        'outline' => [
                            'borderStyle' => $border->outlineBorderStyle,
                            'color' => ['rgb' => '000000'],
                        ],
                        'inside' => [
                            'borderStyle' => $border->insideBorderStyle,
                            'color' => ['rgb' => '000000'],
                        ]
                    ]
                ]);
            }

            if ($fileFormat !== 'Mpdf') {
                $categories = [];
                foreach ($this->graph->categories as $area => $label) {
                    $categories[] = new DataSeriesValues('String', $area, null, 1);
                }
                $values = [];
                $valueLabels = [];
                foreach ($this->graph->values as $area => $label) {
                    $values[] = new DataSeriesValues('Number', $area, null, 1);
                    $valueLabels[] = new DataSeriesValues(DataSeriesValues::DATASERIES_TYPE_STRING, $label, null);
                }
                $dataSeries = new DataSeries(
                    $this->graph->type,
                    DataSeries::GROUPING_CLUSTERED,
                    range(0, count($values) - 1),
                    $valueLabels,
                    $categories,
                    $values,
                );
                $dataSeries->setPlotDirection(DataSeries::DIRECTION_COL);

                $plotArea = new PlotArea(null, [$dataSeries]);
                $legend = new Legend(Legend::POSITION_RIGHT, null, false);
                $title = new Title($this->graph->title);
                $xAxisLabel = new Title($this->graph->xAxisLabel);
                $yAxisLabel = new Title($this->graph->yAxisLabel);

                $chart = new Chart(
                    'chart1',
                    $title,
                    $legend,
                    $plotArea,
                    true,
                    0,
                    $xAxisLabel,
                    $yAxisLabel,
                );

                $chart->setTopLeftPosition('H7');
                $chart->setBottomRightPosition('M18');

                $sheet->addChart($chart);
            }
        }

        $writer = IOFactory::createWriter($doc, $fileFormat);
        if ($result) {
            $writer->setIncludeCharts(true);
        }
        if ($writer instanceof Pdf) {
            StringHelper::setDecimalSeparator(',');
            StringHelper::setThousandsSeparator(' ');
            Settings::setChartRenderer(MtJpGraphRenderer::class);
            $writer->setOrientation(PageSetup::ORIENTATION_LANDSCAPE);
            @mkdir(TEMP_DIR . '/mpdf');
            $writer->setTempDir(TEMP_DIR . '/mpdf');
        }
        $writer->save($filename);
    }

    /**
     * Vytvoří strojově čitelný popis zadání ve formátu JSON.
     *
     * @return string JSON obsahující popis zadání
     */
    public function createJsonDescription(): string
    {
        $data = [
            'cells' => [],
            'borders' => []
        ];

        foreach ($this->cells as $cellName => $cell) {
            $cellData = [
                'style' => [
                    'bold' => $cell->bold,
                    'alignment' => $cell->alignment,
                    'numberFormat' => $cell->numberFormat,
                ]
            ];
            if ($cell->expression !== null) {
                $cellData['expression'] = $cell->expression;
            }
            if ($cell->value !== null) {
                $cellData['input'] = $cell->value;
            }
            foreach ($cell->conditionalFormat as $condition) {
                $cellData['conditionalFormat'][] = [
                    'type' => $condition->type,
                    'operator' => $condition->operator,
                    'value' => $condition->value,
                    'fillColor' => $condition->fillColor,
                    'textColor' => $condition->textColor,
                ];
            }

            $data['cells'][$cellName] = $cellData;
        }
        foreach ($this->borders as $border) {
            $data['borders'][] = [
                'location' => $border->location,
                'outlineBorderStyle' => $border->outlineBorderStyle,
                'insideBorderStyle' => $border->insideBorderStyle,
            ];
        }
        if (isset($this->graph)) {
            $data['chart'] = [
                'type' => $this->graph->type,
                'title' => $this->graph->title,
                'categories' => $this->graph->categories,
                'values' => $this->graph->values,
                'xAxisLabel' => $this->graph->xAxisLabel,
                'yAxisLabel' => $this->graph->yAxisLabel,
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
        $text = "Samostatná práce 2
==================

1) Otevřete soubor $this->identifier.xlsx v Microsoft Excel nebo $this->identifier.ods v LibreOffice Calc. Uvnitř souboru najdete data, se kterými budete pracovat. Veškerý postup ukládejte do tohoto souboru a tento soubor také odevzdejte. Nové soubory nevytvářejte!
2) Na vyznačená místa v souboru doplňte vhodné vzorce k vypočítání požadovaných hodnot. Podbarvení těchto buněk následně zrušte.
3) $this->expressionDescription
4) Dle charakteru dat naformátujte všechny číselné hodnoty na shodný počet desetinných míst a s oddělovačem tisíců.
5) Vhodně naformátujte všechny tabulky. Záhlaví sloupců nastavte tučně, použijte horizontální a vertikální zarovnání. Nastavte ohraničení buněk v tabulce dvou typů - tlusté pro vnější a tenké pro vnitřní hrany.
6) Vytvořte podmíněné formátování
";
        foreach ($this->conditionalFormatDescription as $condition) {
                $text .= "    - " . $condition . "\n";
        }

        $text .= "7) {$this->graph->description}
8) Ověřte si splnění všech bodů zadání.
9) Dokument uložte a před odevzdáním zavřete.";
        return $text;
    }
}