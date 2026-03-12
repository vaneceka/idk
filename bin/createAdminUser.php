<?php

/**
 * Soubor sloužící pro vytvoření nového administrátorského uživatele.
 *
 * @author Michal Turek
 */

use App\Model\Database\DatabaseManager;

const ROOT_DIR = __DIR__ . '/..';

require_once __DIR__ . '/../vendor/autoload.php';
require_once __DIR__ . '/../config/conf.inc.php';

$database = new DatabaseManager();
$result = $database->createAdminUser(readline('Username: '), readline('Name: '), readline('Surname: '), readline('Password: '), 1);
if ($result !== false) {
    echo 'Admin user created: ' . $result . PHP_EOL;
} else {
    echo 'Error' . PHP_EOL;
}

