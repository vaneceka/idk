<?php

namespace App\Generator\Spreadsheet;

use PhpOffice\PhpSpreadsheet\Chart\DataSeries;
use PhpOffice\PhpSpreadsheet\Style\Border;
use PhpOffice\PhpSpreadsheet\Style\Conditional;

/**
 * Generátor zadání porovnávání BMI jednotlivých pacientů.
 *
 * @author Michal Turek
 */
class DiagnosisSpreadsheetGenerator implements SpreadsheetGenerator
{
    public function generate(string $identifier, int $minRows, int $maxRows): Spreadsheet
    {
        $spreadsheet = new Spreadsheet();
        $spreadsheet->identifier = $identifier;

        $expressionVariation = rand(1, 4);

        // Záhlaví tabulky
        $spreadsheet->cells['A1'] = new Cell('Diagnóza', bold: true, alignment: true);
        $spreadsheet->cells['B1'] = new Cell('Počet pacientů', bold: true, alignment: true);
        $spreadsheet->cells['C1'] = new Cell('Procento z celkového počtu', bold: true, alignment: true);
        $spreadsheet->cells['D1'] = new Cell(match ($expressionVariation) {
            1 => 'Počet nad průměrem',
            2 => 'Počet pod průměrem',
            3 => 'Počet nad střední hodnotou',
            4 => 'Počet pod střední hodnotou',
        }, bold: true, alignment: true);

        $rowCount = rand($minRows, $maxRows);

        $conditions = [
            new ConditionalFormat(Conditional::CONDITION_CELLIS, Conditional::OPERATOR_LESSTHAN, 18.5, fillColor: '5981C2'),
            new ConditionalFormat(Conditional::CONDITION_CELLIS, Conditional::OPERATOR_GREATERTHAN, 25, textColor: 'FF0000'),
        ];
        $spreadsheet->conditionalFormatDescription = [
            'pro zvýraznění takového počtu pacientů, který přesahuje 15, změňte barvu pozadí na červenou.',
            'pro zvýraznění takového počtu pacientů, který je menší než 10, změňte barvu textu na modrou.',
        ];

        $spreadsheet->expressionDescription = match ($expressionVariation) {
            1 => 'V sloupci "Počet nad průměrem" použijte vzorec, ve kterém porovnáte počet diagnóz v řádku s průměrnou hodnotou. Zobrazíte slovo "více", jestliže je hodnota ostře větší než průměr. Jinak bude zobrazeno slovo "ne".',
            2 => 'V sloupci "Počet pod průměrem" použijte vzorec, ve kterém porovnáte počet diagnóz v řádku s průměrnou hodnotou. Zobrazíte slovo "méně", jestliže je hodnota ostře menší než průměr. Jinak bude zobrazeno slovo "ne".',
            3 => 'V sloupci "Počet nad střední hodnotou" použijte vzorec, ve kterém porovnáte počet diagnóz v řádku se střední hodnotou. Zobrazíte slovo "více", jestliže je hodnota ostře větší než střední hodnota. Jinak bude zobrazeno slovo "ne".',
            4 => 'V sloupci "Počet pod střední hodnotou" použijte vzorec, ve kterém porovnáte počet diagnóz v řádku se střední hodnotou. Zobrazíte slovo "méně", jestliže je hodnota ostře menší než střední hodnota. Jinak bude zobrazeno slovo "ne".',
        };

        $tableStart = $rowCount + 5;

        $diagnoses = ['Zápal plic', 'Infarkt', 'Zlomenina', 'Operace slepého střeva', 'COVID-19'];
        $usage = [];

        for ($i = 1; $i <= $rowCount; $i++) {
            $row = $i + 1;
            $diagnose = $diagnoses[array_rand($diagnoses)];
            if (isset($usage[$diagnose])) {
                $diagnose .= ' ' . (++$usage[$diagnose]);
            } else {
                $usage[$diagnose] = 1;
            }

            $spreadsheet->cells['A' . $row] = new Cell($diagnose);
            $spreadsheet->cells['B' . $row] = new Cell(rand(5, 20), numberFormat: '#,##0.0', conditionalFormat: $conditions);
            $spreadsheet->cells['C' . $row] = new Cell(expression: '=B' . $row . '/F$' . ($tableStart + 1), numberFormat: '%#,##0.00');

            $spreadsheet->cells['D' . $row] = new Cell(expression: match ($expressionVariation) {
                1 => '=IF(D$' . ($tableStart + 1) . '>B' . $row . ',"ne","více")',
                2 => '=IF(D$' . ($tableStart + 1) . '<=B' . $row . ',"ne","méně")',
                3 => '=IF(E$' . ($tableStart + 1) . '>B' . $row . ',"ne","více")',
                4 => '=IF(E$' . ($tableStart + 1) . '<=B' . $row . ',"ne","méně")',
            });
        }

        // Agregace
        $spreadsheet->cells['B' . $tableStart] = new Cell('Minimum', bold: true, alignment: true);
        $spreadsheet->cells['C' . $tableStart] = new Cell('Maximum', bold: true, alignment: true);
        $spreadsheet->cells['D' . $tableStart] = new Cell('Průměr', bold: true, alignment: true);
        $spreadsheet->cells['E' . $tableStart] = new Cell('Střední hodnota', bold: true, alignment: true);
        $spreadsheet->cells['F' . $tableStart] = new Cell('Suma', bold: true, alignment: true);

        $spreadsheet->cells['A' . ($tableStart + 1)] = new Cell('Počet', bold: true);

        $spreadsheet->cells['B' . ($tableStart + 1)] = new Cell(expression: '=MIN(B2:B' . ($rowCount + 1) . ')', numberFormat: '#,##0.00');
        $spreadsheet->cells['C' . ($tableStart + 1)] = new Cell(expression: '=MAX(B2:B' . ($rowCount + 1) . ')', numberFormat: '#,##0.00');
        $spreadsheet->cells['D' . ($tableStart + 1)] = new Cell(expression: '=AVERAGE(B2:B' . ($rowCount + 1) . ')', numberFormat: '#,##0.00');
        $spreadsheet->cells['E' . ($tableStart + 1)] = new Cell(expression: '=MEDIAN(B2:B' . ($rowCount + 1) . ')', numberFormat: '#,##0.00');
        $spreadsheet->cells['F' . ($tableStart + 1)] = new Cell(expression: '=SUM(B2:B' . ($rowCount + 1) . ')', numberFormat: '#,##0.00');

        $spreadsheet->borders[] = new BorderedSection('A1:D' . ($rowCount + 1), Border::BORDER_THICK, Border::BORDER_THIN);
        $spreadsheet->borders[] = new BorderedSection('A' . ($tableStart) . ':F' . ($tableStart + 1), Border::BORDER_THICK, Border::BORDER_THIN);

        $spreadsheet->graph = new Graph(
            'Počet pacientů',
            DataSeries::TYPE_BARCHART,
            ['data!$A$2:$A$' . ($rowCount + 1) => 'data!$A$1'],
            ['data!$B$2:$B$' . ($rowCount + 1) => 'data!$B$1'],
            'Vytvořte sloupcový graf, který bude porovnávat počet pacientů podle jednotlivých diagnóz.',
            'Diagnóza',
            'Počet pacientů',
        );

        return $spreadsheet;
    }
}