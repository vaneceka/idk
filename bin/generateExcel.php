<?php

/**
 * Soubor s příkladem využití generátoru zadání pro tabulkový procesor.
 *
 * @author Michal Turek
 */

require_once __DIR__ . '/../vendor/autoload.php';

$generator = new \App\Generator\Spreadsheet\BmiSpreadsheetGenerator();
$document = $generator->generate('Z24B9999P', 15, 22);

$folder = __DIR__ . '/../test/excel-' . date('Y-m-d-H-i-s');
@mkdir($folder, recursive: true);
$document->createSourceFile($folder . '/' . $document->identifier . '.xlsx', 'Xlsx');
$document->createSourceFile($folder . '/' . $document->identifier . '.ods', 'Ods');
$document->createSourceFile($folder . '/' . $document->identifier . '-result.xlsx', 'Xlsx', true);
$document->createSourceFile($folder . '/' . $document->identifier . '-result.pdf', 'Mpdf', true);
file_put_contents($folder . '/assignment.json', $document->createJsonDescription());
file_put_contents($folder . '/zadani.txt', $document->createAssignmentDescription());