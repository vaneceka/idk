<?php

declare(strict_types=1);

namespace App\Model\Database\Types;

/**
 * Konstanty pro globální nastavení systému
 *
 * @author Michal Turek
 */
final class Options
{
    /**
     * Aktuální akademický rok
     */
    public const string YEAR = 'year';
    /**
     * Aktuální semestr
     */
    public const string SEMESTER = 'semester';
}