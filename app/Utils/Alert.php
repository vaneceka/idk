<?php

declare(strict_types=1);

namespace App\Utils;

/**
 * Stavová zpráva zobrazená v šabloně po provedení nějaké akce.
 *
 * @author Michal Turek
 */
readonly class Alert
{
    /**
     * @param string $message zobrazená zpráva
     * @param string $class css třída pro konkrétní podbarvení stavové zprávy (například success nebo danger)
     */
    public function __construct(
        public string $message,
        public string $class,
    ) {
    }
}