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
class BmiSpreadsheetGenerator implements SpreadsheetGenerator
{
    public function generate(string $identifier, int $minRows, int $maxRows): Spreadsheet
    {
        $spreadsheet = new Spreadsheet();
        $spreadsheet->identifier = $identifier;

        $expressionVariation = rand(1, 4);

        // Záhlaví tabulky
        $spreadsheet->cells['A1'] = new Cell('Pacient', bold: true, alignment: true);
        $spreadsheet->cells['B1'] = new Cell('Pohlaví', bold: true, alignment: true);
        $spreadsheet->cells['C1'] = new Cell('Výška (cm)', bold: true, alignment: true);
        $spreadsheet->cells['D1'] = new Cell('Váha (kg)', bold: true, alignment: true);
        $spreadsheet->cells['E1'] = new Cell('BMI', bold: true, alignment: true);
        $spreadsheet->cells['F1'] = new Cell(match ($expressionVariation) {
            1 => 'BMI nad průměrem',
            2 => 'BMI pod průměrem',
            3 => 'BMI nad střední hodnotou',
            4 => 'BMI pod střední hodnotou',
        }, bold: true, alignment: true);

        $patientCount = rand($minRows, $maxRows);

        $conditions = [
            new ConditionalFormat(Conditional::CONDITION_CELLIS, Conditional::OPERATOR_LESSTHAN, 18.5, fillColor: '5981C2'),
            new ConditionalFormat(Conditional::CONDITION_CELLIS, Conditional::OPERATOR_GREATERTHAN, 25, textColor: 'FF0000'),
        ];
        $spreadsheet->conditionalFormatDescription = [
            'pro zvýraznění takových hodnot BMI, která značí podváhu (< 18,5) změnou barvy pozadí na světle modrou.',
            'pro zvýraznění takových hodnot BMI, která značí nadváhu či obezitu (> 25) změnou barvy textu na červenou.',
        ];

        $spreadsheet->expressionDescription = match ($expressionVariation) {
            1 => 'V sloupci "BMI nad průměrem" použijte vzorec, ve kterém porovnáte hodnotu BMI v řádku s průměrnou hodnotou. Zobrazíte slovo "více", jestliže je hodnota ostře větší než průměr. Jinak bude zobrazeno slovo "ne".',
            2 => 'V sloupci "BMI pod průměrem" použijte vzorec, ve kterém porovnáte hodnotu BMI v řádku s průměrnou hodnotou. Zobrazíte slovo "méně", jestliže je hodnota ostře menší než průměr. Jinak bude zobrazeno slovo "ne".',
            3 => 'V sloupci "BMI nad střední hodnotou" použijte vzorec, ve kterém porovnáte hodnotu BMI v řádku se střední hodnotou. Zobrazíte slovo "více", jestliže je hodnota ostře větší než střední hodnota. Jinak bude zobrazeno slovo "ne".',
            4 => 'V sloupci "BMI pod střední hodnotou" použijte vzorec, ve kterém porovnáte hodnotu BMI v řádku se střední hodnotou. Zobrazíte slovo "méně", jestliže je hodnota ostře menší než střední hodnota. Jinak bude zobrazeno slovo "ne".',
        };

        $tableStart = $patientCount + 5;

        for ($i = 1; $i <= $patientCount; $i++) {
            $row = $i + 1;
            $spreadsheet->cells['A' . $row] = new Cell($i);
            $spreadsheet->cells['B' . $row] = new Cell(rand(0, 1) === 1 ? 'muž' : 'žena');
            $spreadsheet->cells['C' . $row] = new Cell(rand(1580, 1900) / 10, numberFormat: '#,##0.0');
            $spreadsheet->cells['D' . $row] = new Cell(rand(500, 1300) / 10, numberFormat: '#,##0.0');
            $spreadsheet->cells['E' . $row] = new Cell(
                expression: '=D' . $row . '/(C' . $row . '/100)^2',
                numberFormat: '#,##0.0',
                conditionalFormat: $conditions,
            );

            $spreadsheet->cells['F' . $row] = new Cell(expression: match ($expressionVariation) {
                1 => '=IF(D$' . ($tableStart + 3) . '>E' . $row . ',"ne","více")',
                2 => '=IF(D$' . ($tableStart + 3) . '<=E' . $row . ',"ne","méně")',
                3 => '=IF(E$' . ($tableStart + 3) . '>E' . $row . ',"ne","více")',
                4 => '=IF(E$' . ($tableStart + 3) . '<=E' . $row . ',"ne","méně")',
            });
        }

        // Agregace
        $spreadsheet->cells['B' . $tableStart] = new Cell('Minimum', bold: true, alignment: true);
        $spreadsheet->cells['C' . $tableStart] = new Cell('Maximum', bold: true, alignment: true);
        $spreadsheet->cells['D' . $tableStart] = new Cell('Průměr', bold: true, alignment: true);
        $spreadsheet->cells['E' . $tableStart] = new Cell('Střední hodnota', bold: true, alignment: true);

        $spreadsheet->cells['A' . ($tableStart + 1)] = new Cell('Výška', bold: true);
        $spreadsheet->cells['A' . ($tableStart + 2)] = new Cell('Váha', bold: true);
        $spreadsheet->cells['A' . ($tableStart + 3)] = new Cell('BMI', bold: true);

        $spreadsheet->cells['B' . ($tableStart + 1)] = new Cell(expression: '=MIN(C2:C' . ($patientCount + 1) . ')', numberFormat: '#,##0.00');
        $spreadsheet->cells['C' . ($tableStart + 1)] = new Cell(expression: '=MAX(C2:C' . ($patientCount + 1) . ')', numberFormat: '#,##0.00');
        $spreadsheet->cells['D' . ($tableStart + 1)] = new Cell(expression: '=AVERAGE(C2:C' . ($patientCount + 1) . ')', numberFormat: '#,##0.00');
        $spreadsheet->cells['E' . ($tableStart + 1)] = new Cell(expression: '=MEDIAN(C2:C' . ($patientCount + 1) . ')', numberFormat: '#,##0.00');

        $spreadsheet->cells['B' . ($tableStart + 2)] = new Cell(expression: '=MIN(D2:D' . ($patientCount + 1) . ')', numberFormat: '#,##0.00');
        $spreadsheet->cells['C' . ($tableStart + 2)] = new Cell(expression: '=MAX(D2:D' . ($patientCount + 1) . ')', numberFormat: '#,##0.00');
        $spreadsheet->cells['D' . ($tableStart + 2)] = new Cell(expression: '=AVERAGE(D2:D' . ($patientCount + 1) . ')', numberFormat: '#,##0.00');
        $spreadsheet->cells['E' . ($tableStart + 2)] = new Cell(expression: '=MEDIAN(D2:D' . ($patientCount + 1) . ')', numberFormat: '#,##0.00');

        $spreadsheet->cells['B' . ($tableStart + 3)] = new Cell(expression: '=MIN(E2:E' . ($patientCount + 1) . ')', numberFormat: '#,##0.00');
        $spreadsheet->cells['C' . ($tableStart + 3)] = new Cell(expression: '=MAX(E2:E' . ($patientCount + 1) . ')', numberFormat: '#,##0.00');
        $spreadsheet->cells['D' . ($tableStart + 3)] = new Cell(expression: '=AVERAGE(E2:E' . ($patientCount + 1) . ')', numberFormat: '#,##0.00');
        $spreadsheet->cells['E' . ($tableStart + 3)] = new Cell(expression: '=MEDIAN(E2:E' . ($patientCount + 1) . ')', numberFormat: '#,##0.00');

        $spreadsheet->borders[] = new BorderedSection('A1:F' . ($patientCount + 1), Border::BORDER_THICK, Border::BORDER_THIN);
        $spreadsheet->borders[] = new BorderedSection('A' . ($tableStart) . ':E' . ($tableStart + 3), Border::BORDER_THICK, Border::BORDER_THIN);

        $spreadsheet->graph = match (rand(1, 3)) {
            1 => new Graph(
                'Výška pacientů',
                DataSeries::TYPE_BARCHART,
                ['data!$A$2:$A$' . ($patientCount + 1) => 'data!$A$1'],
                ['data!$C$2:$C$' . ($patientCount + 1) => 'data!$C$1'],
                'Vytvořte sloupcový graf, který bude porovnávat výšku jednotlivých pacientů.',
                'Pacient',
                'Výška',
            ),
            2 => new Graph(
                'Váha pacientů',
                DataSeries::TYPE_BARCHART,
                ['data!$A$2:$A$' . ($patientCount + 1) => 'data!$A$1'],
                ['data!$D$2:$D$' . ($patientCount + 1) => 'data!$D$1'],
                'Vytvořte sloupcový graf, který bude porovnávat váhu jednotlivých pacientů.',
                'Pacient',
                'Váha',
            ),
            3 => new Graph(
                'BMI pacientů',
                DataSeries::TYPE_BARCHART,
                ['data!$A$2:$A$' . ($patientCount + 1) => 'data!$A$1'],
                ['data!$E$2:$E$' . ($patientCount + 1) => 'data!$E$1'],
                'Vytvořte sloupcový graf, který bude porovnávat BMI jednotlivých pacientů.',
                'Pacient',
                'BMI',
            ),
        };

        return $spreadsheet;
    }
}