<?php

/**
 * Soubor sloužící pro inicializaci databázové struktury.
 *
 * @author Michal Turek
 */

const ROOT_DIR = __DIR__ . '/..';

require_once __DIR__ . '/../config/conf.inc.php';

$pdo = new PDO('mysql:host=' . DB_HOST . ';dbname=' . DB_NAME, DB_USER, DB_PASSWORD);
$pdo->exec("set names utf8");
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

$pdo->exec(file_get_contents(ROOT_DIR . '/structure.sql'));
