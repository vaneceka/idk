<?php

declare(strict_types=1);

namespace App\Controller;

/**
 * Chybový Controller, na který se aplikace přesměrovává při požadavku klienta na neznámý controller.
 *
 * @author Michal Turek
 */
class ErrorController extends Controller
{
    protected function process(): void
    {
    }
}
