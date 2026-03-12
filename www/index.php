<?php
declare(strict_types=1);

// ===== HARD DEBUG MODE (temporary) =====
ini_set('display_errors', '1');
ini_set('display_startup_errors', '1');
ini_set('html_errors', '0');           // ať to není HTML bordel
ini_set('log_errors', '1');            // ať se to zároveň loguje
error_reporting(E_ALL);

// Když je už něco posláno do outputu, občas to “schová” chybu.
// Proto buffer – a při chybě ho vypláchneme.
ob_start();

function debug_print_exception(Throwable $e): void {
    // vyčisti output buffer, ať je vidět chyba (ne HTML stránky apod.)
    while (ob_get_level() > 0) {
        ob_end_clean();
    }

    http_response_code(500);
    header('Content-Type: text/plain; charset=utf-8');

    echo "UNCAUGHT EXCEPTION: " . get_class($e) . "\n";
    echo $e->getMessage() . "\n\n";
    echo $e->getFile() . ":" . $e->getLine() . "\n\n";
    echo $e->getTraceAsString() . "\n";
    exit;
}

set_exception_handler('debug_print_exception');

// Převést warnings/notices na výjimky (E_DEPRECATED si můžeš klidně vyhodit, když to spamuje)
set_error_handler(function (int $severity, string $message, string $file, int $line): bool {
    // některé chyby můžou být potlačené @ operátorem
    if (!(error_reporting() & $severity)) {
        return true;
    }
    throw new ErrorException($message, 0, $severity, $file, $line);
});

// Zachytí fatal errors (Parse error, fatal TypeError mimo try/catch, atd.)
register_shutdown_function(function (): void {
    $err = error_get_last();
    if (!$err) {
        // žádný fatal error => normální výstup
        return;
    }

    $fatalTypes = [E_ERROR, E_PARSE, E_CORE_ERROR, E_COMPILE_ERROR, E_USER_ERROR];
    if (!in_array($err['type'], $fatalTypes, true)) {
        return;
    }

    while (ob_get_level() > 0) {
        ob_end_clean();
    }

    http_response_code(500);
    header('Content-Type: text/plain; charset=utf-8');

    echo "FATAL ERROR\n";
    echo $err['message'] . "\n\n";
    echo $err['file'] . ":" . $err['line'] . "\n";
    exit;
});

// ===== App bootstrap =====
const ROOT_DIR = __DIR__ . '/..';

require_once __DIR__ . '/../vendor/autoload.php';
require_once __DIR__ . '/../config/conf.inc.php';

// dočasně vypnout Tracy, ať do toho neleze
// \Tracy\Debugger::enable(DEBUGGER ? \Tracy\Debugger::Development : \Tracy\Debugger::Production);

\App\Router::processRequest();