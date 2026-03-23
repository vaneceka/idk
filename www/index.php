<?php

use App\Router;
use Tracy\Debugger;

const ROOT_DIR = __DIR__ . '/..';

require_once __DIR__ . '/../vendor/autoload.php';
require_once __DIR__ . '/../config/conf.inc.php';

Tracy\Debugger::enable(DEBUGGER ? Debugger::Development : Debugger::Production);

/**
 * Vstupní bod aplikace.
 */
Router::processRequest();