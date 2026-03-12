<?php

namespace App\Generator\Spreadsheet;

use PhpOffice\PhpSpreadsheet\Chart\DataSeries;
use PhpOffice\PhpSpreadsheet\Style\Border;
use PhpOffice\PhpSpreadsheet\Style\Conditional;

/**
 * Generátor zadání pro porovnávání krevního tlaku pacientů.
 *
 * @author Michal Turek
 */
class BloodPressureSpreadsheetGenerator implements SpreadsheetGenerator
{
    public function generate(string $identifier, int $minRows, int $maxRows): Spreadsheet
    {
        $spreadsheet = new Spreadsheet();
        $spreadsheet->identifier = $identifier;

        $expressionVariation = rand(1, 4);

        // Záhlaví tabulky
        $spreadsheet->cells['A1'] = new Cell('Pacient', bold: true, alignment: true);
        $spreadsheet->cells['B1'] = new Cell('Pohlaví', bold: true, alignment: true);
        $spreadsheet->cells['C1'] = new Cell('Systolický tlak (mmHg)', bold: true, alignment: true);
        $spreadsheet->cells['D1'] = new Cell('Diastolický tlak (mmHg)', bold: true, alignment: true);
        $spreadsheet->cells['E1'] = new Cell('Pulzní tlak', bold: true, alignment: true);
        $spreadsheet->cells['F1'] = new Cell(match ($expressionVariation) {
            1 => 'Systolický tlak nad průměrem',
            2 => 'Systolický tlak pod průměrem',
            3 => 'Diastolický tlak nad střední hodnotou',
            4 => 'Diastolický tlak pod střední hodnotou',
        }, bold: true, alignment: true);

        $patientCount = rand($minRows, $maxRows);

        $spreadsheet->conditionalFormatDescription = [
            'pro zvýraznění hodnot systolického tlaku nad 140 mmHg změnou barvy textu na červenou.',
            'pro zvýraznění hodnot diastolického tlaku pod 90 mmHg změnou barvy pozadí na světle modrou.',
        ];

        $spreadsheet->expressionDescription = match ($expressionVariation) {
            1 => 'V sloupci "Systolický tlak nad průměrem" použijte vzorec, ve kterém porovnáte hodnotu systolického tlaku v řádku s průměrnou hodnotou. Zobrazíte slovo "více", jestliže je hodnota ostře větší než průměr. Jinak bude zobrazeno slovo "ne".',
            2 => 'V sloupci "Systolický tlak pod průměrem" použijte vzorec, ve kterém porovnáte hodnotu systolického tlaku v řádku s průměrnou hodnotou. Zobrazíte slovo "méně", jestliže je hodnota ostře menší než průměr. Jinak bude zobrazeno slovo "ne".',
            3 => 'V sloupci "Diastolický tlak nad střední hodnotou" použijte vzorec, ve kterém porovnáte hodnotu diastolického tlaku v řádku se střední hodnotou. Zobrazíte slovo "více", jestliže je hodnota ostře větší než střední hodnota. Jinak bude zobrazeno slovo "ne".',
            4 => 'V sloupci "Diastolický tlak pod střední hodnotou" použijte vzorec, ve kterém porovnáte hodnotu diastolického tlaku v řádku se střední hodnotou. Zobrazíte slovo "méně", jestliže je hodnota ostře menší než střední hodnota. Jinak bude zobrazeno slovo "ne".',
        };

        $tableStart = $patientCount + 5;

        for ($i = 1; $i <= $patientCount; $i++) {
            $row = $i + 1;
            $systolic = rand(85, 180);
            $diastolic = rand(50, min(110, $systolic - 10));

            $spreadsheet->cells['A' . $row] = new Cell($i);
            $spreadsheet->cells['B' . $row] = new Cell(rand(0, 1) === 1 ? 'muž' : 'žena');
            $spreadsheet->cells['C' . $row] = new Cell($systolic, numberFormat: '#,##0.00', conditionalFormat: [
                new ConditionalFormat(Conditional::CONDITION_CELLIS, Conditional::OPERATOR_GREATERTHAN, 140, textColor: 'FF0000'),
            ]);
            $spreadsheet->cells['D' . $row] = new Cell($diastolic, numberFormat: '#,##0.00', conditionalFormat: [
                new ConditionalFormat(Conditional::CONDITION_CELLIS, Conditional::OPERATOR_LESSTHAN, 90, fillColor: '5981C2'),
            ]);
            $spreadsheet->cells['E' . $row] = new Cell(expression: '=C' . $row . ' - D' . $row);

            $spreadsheet->cells['F' . $row] = new Cell(expression: match ($expressionVariation) {
                1 => '=IF(D$' . ($tableStart + 1) . '>C' . $row . ',"ne","více")',
                2 => '=IF(D$' . ($tableStart + 1) . '<=C' . $row . ',"ne","méně")',
                3 => '=IF(E$' . ($tableStart + 2) . '>D' . $row . ',"ne","více")',
                4 => '=IF(E$' . ($tableStart + 2) . '<=D' . $row . ',"ne","méně")',
            });
        }

        // Agregace
        $spreadsheet->cells['B' . $tableStart] = new Cell('Minimum', bold: true, alignment: true);
        $spreadsheet->cells['C' . $tableStart] = new Cell('Maximum', bold: true, alignment: true);
        $spreadsheet->cells['D' . $tableStart] = new Cell('Průměr', bold: true, alignment: true);
        $spreadsheet->cells['E' . $tableStart] = new Cell('Střední hodnota', bold: true, alignment: true);

        $spreadsheet->cells['A' . ($tableStart + 1)] = new Cell('Systolický tlak', bold: true);
        $spreadsheet->cells['A' . ($tableStart + 2)] = new Cell('Diastolický tlak', bold: true);
        $spreadsheet->cells['A' . ($tableStart + 3)] = new Cell('Pulzní tlak', bold: true);

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

        $spreadsheet->graph = match (rand(1, 2)) {
            1 => new Graph(
                'Systolický tlak pacientů',
                DataSeries::TYPE_BARCHART,
                ['data!$A$2:$A$' . ($patientCount + 1) => 'data!$A$1'],
                ['data!$C$2:$C$' . ($patientCount + 1) => 'data!$C$1'],
                'Vytvořte sloupcový graf, který bude porovnávat systolický tlak jednotlivých pacientů.',
                'Pacient',
                'Systolický tlak',
            ),
            2 => new Graph(
                'Diastolický tlak pacientů',
                DataSeries::TYPE_BARCHART,
                ['data!$A$2:$A$' . ($patientCount + 1) => 'data!$A$1'],
                ['data!$D$2:$D$' . ($patientCount + 1) => 'data!$D$1'],
                'Vytvořte sloupcový graf, který bude porovnávat diastolický tlak jednotlivých pacientů.',
                'Pacient',
                'Diastolický tlak',
            ),
        };

        return $spreadsheet;
    }
}
