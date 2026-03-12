<?php

/**
 * Soubor s příkladem využití generátoru zadání pro textový procesor.
 *
 * @author Michal Turek
 */

require_once __DIR__ . '/../vendor/autoload.php';

$generator = new \App\Generator\TextDocument\TextDocumentGenerator(0);
$document = $generator->generate('Michal Turek', 'Z24B9999P');

$folder = __DIR__ . '/../test/test-' . date('Y-m-d-H-i-s');
@mkdir($folder, recursive: true);
$document->createSourceFile($folder . '/' . $document->identifier . '.docx', 'Word2007');
$document->createSourceFile($folder . '/' . $document->identifier . '.odt', 'ODText');
file_put_contents($folder . '/assignment.json', $document->createJsonDescription());
file_put_contents($folder . '/zadani.txt', $document->createAssignmentDescription());
$document->createResultFile($folder . '/result.pdf');
foreach ($document->objects as $object) {
    copy($object->file, $folder . '/' . $object->identifier . '.png');
}