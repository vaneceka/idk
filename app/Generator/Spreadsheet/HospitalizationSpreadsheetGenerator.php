<?php

namespace App\Generator\Spreadsheet;

use PhpOffice\PhpSpreadsheet\Chart\DataSeries;
use PhpOffice\PhpSpreadsheet\Style\Border;
use PhpOffice\PhpSpreadsheet\Style\Conditional;

/**
 * Generátor zadání porovnávající délku hospitalizace pacientů.
 *
 * @author Michal Turek
 */
class HospitalizationSpreadsheetGenerator implements SpreadsheetGenerator
{
    public function generate(string $identifier, int $minRows, int $maxRows): Spreadsheet
    {
        $spreadsheet = new Spreadsheet();
        $spreadsheet->identifier = $identifier;

        $expressionVariation = rand(1, 4);

        // Záhlaví tabulky
        $spreadsheet->cells['A1'] = new Cell('Pacient', bold: true, alignment: true);
        $spreadsheet->cells['B1'] = new Cell('Pohlaví', bold: true, alignment: true);
        $spreadsheet->cells['C1'] = new Cell('Diagnóza', bold: true, alignment: true);
        $spreadsheet->cells['D1'] = new Cell('Doba hospitalizace (dny)', bold: true, alignment: true);
        $spreadsheet->cells['E1'] = new Cell(match ($expressionVariation) {
            1 => 'Doba nad průměrem',
            2 => 'Doba pod průměrem',
            3 => 'Doba nad střední hodnotou',
            4 => 'Doba pod střední hodnotou',
        }, bold: true, alignment: true);

        $diagnoses = ['Zápal plic', 'Infarkt', 'Zlomenina', 'Operace slepého střeva', 'COVID-19'];
        $patientCount = rand($minRows, $maxRows);

        $conditions = [
            new ConditionalFormat(Conditional::CONDITION_CELLIS, Conditional::OPERATOR_GREATERTHAN, 14, fillColor: 'FF9999'),
            new ConditionalFormat(Conditional::CONDITION_CELLIS, Conditional::OPERATOR_BETWEEN, '7,14', fillColor: 'FFFF99'),
        ];

        $spreadsheet->conditionalFormatDescription = [
            'pro zvýraznění dlouhých hospitalizací (> 14 dní) červeným pozadím.',
            'pro zvýraznění středně dlouhých hospitalizací (7-14 dní) žlutým pozadím.',
        ];

        $spreadsheet->expressionDescription = match ($expressionVariation) {
            1 => 'V sloupci "Doba nad průměrem" použijte vzorec, ve kterém porovnáte dobu hospitalizace v řádku s průměrnou hodnotou. Zobrazíte slovo "více", jestliže je hodnota ostře větší než průměr. Jinak bude zobrazeno slovo "ne".',
            2 => 'V sloupci "Doba pod průměrem" použijte vzorec, ve kterém porovnáte dobu hospitalizace v řádku s průměrnou hodnotou. Zobrazíte slovo "méně", jestliže je hodnota ostře menší než průměr. Jinak bude zobrazeno slovo "ne".',
            3 => 'V sloupci "Doba nad střední hodnotou" použijte vzorec, ve kterém porovnáte dobu hospitalizace v řádku se střední hodnotou. Zobrazíte slovo "více", jestliže je hodnota ostře větší než střední hodnota. Jinak bude zobrazeno slovo "ne".',
            4 => 'V sloupci "Doba pod střední hodnotou" použijte vzorec, ve kterém porovnáte dobu hospitalizace v řádku se střední hodnotou. Zobrazíte slovo "méně", jestliže je hodnota ostře menší než střední hodnota. Jinak bude zobrazeno slovo "ne".',
        };

        $tableStart = $patientCount + 5;

        for ($i = 1; $i <= $patientCount; $i++) {
            $row = $i + 1;
            $hospitalDays = rand(2, 30);

            $spreadsheet->cells['A' . $row] = new Cell($i);
            $spreadsheet->cells['B' . $row] = new Cell(rand(0, 1) === 1 ? 'muž' : 'žena');
            $spreadsheet->cells['C' . $row] = new Cell($diagnoses[array_rand($diagnoses)]);
            $spreadsheet->cells['D' . $row] = new Cell($hospitalDays, numberFormat: '0', conditionalFormat: $conditions);
            $spreadsheet->cells['E' . $row] = new Cell(expression: match ($expressionVariation) {
                1 => '=IF(D$' . ($tableStart + 1) . '>D' . $row . ',"ne","více")',
                2 => '=IF(D$' . ($tableStart + 1) . '<=D' . $row . ',"ne","méně")',
                3 => '=IF(E$' . ($tableStart + 1) . '>D' . $row . ',"ne","více")',
                4 => '=IF(E$' . ($tableStart + 1) . '<=D' . $row . ',"ne","méně")',
            });
        }

        // Agregace
        $spreadsheet->cells['B' . $tableStart] = new Cell('Minimum', bold: true, alignment: true);
        $spreadsheet->cells['C' . $tableStart] = new Cell('Maximum', bold: true, alignment: true);
        $spreadsheet->cells['D' . $tableStart] = new Cell('Průměr', bold: true, alignment: true);
        $spreadsheet->cells['E' . $tableStart] = new Cell('Střední hodnota', bold: true, alignment: true);

        $spreadsheet->cells['A' . ($tableStart + 1)] = new Cell('Doba hospitalizace', bold: true);
        $spreadsheet->cells['B' . ($tableStart + 1)] = new Cell(expression: '=MIN(D2:D' . ($patientCount + 1) . ')', numberFormat: '#,##0.00');
        $spreadsheet->cells['C' . ($tableStart + 1)] = new Cell(expression: '=MAX(D2:D' . ($patientCount + 1) . ')', numberFormat: '#,##0.00');
        $spreadsheet->cells['D' . ($tableStart + 1)] = new Cell(expression: '=AVERAGE(D2:D' . ($patientCount + 1) . ')', numberFormat: '#,##0.00');
        $spreadsheet->cells['E' . ($tableStart + 1)] = new Cell(expression: '=MEDIAN(D2:D' . ($patientCount + 1) . ')', numberFormat: '#,##0.00');

        $spreadsheet->borders[] = new BorderedSection('A1:E' . ($patientCount + 1), Border::BORDER_THICK, Border::BORDER_THIN);
        $spreadsheet->borders[] = new BorderedSection('A' . ($tableStart) . ':E' . ($tableStart + 1), Border::BORDER_THICK, Border::BORDER_THIN);

        $spreadsheet->graph = new Graph(
            'Délka hospitalizace pacientů',
            DataSeries::TYPE_BARCHART,
            ['data!$A$2:$A$' . ($patientCount + 1) => 'data!$A$1'],
            ['data!$D$2:$D$' . ($patientCount + 1) => 'data!$D$1'],
            'Vytvořte sloupcový graf, který bude porovnávat dobu hospitalizace jednotlivých pacientů.',
            'Pacient',
            'Doba hospitalizace (dny)',
        );

        return $spreadsheet;
    }
}
