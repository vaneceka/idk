<?php

declare(strict_types=1);

namespace App\Model;

/**
 * Třída sloužící pro práci se session.
 *
 * @author Michal Turek
 */
class Session
{
    /**
     * Klíč pro ukládání zpráv
     */
    public const string ALERTS = 'alerts';
    /**
     * Klíč pro ukládání přihlášeného administrátora/učitele.
     */
    public const string ADMIN = 'admin';

    /**
     * Klíč pro ukládání přihlášeného studenta.
     */
    public const string STUDENT = 'student';

    private bool $initialized = false;

    /**
     * Konstruktor automaticky otevře sezení, pokud byla zaslána session cookie, jinak počká, dokud se do něj nebude chtít zapisovat.
     */
    public function __construct()
    {
        if (isset($_COOKIE[session_name()])) {
            session_start();
            $this->initialized = true;
        }
    }

    /**
     * Vrátí hodnotu ze session
     *
     * @param string $key klíč hodnoty
     * @return mixed hodnota nebo null
     */
    public function get(string $key): mixed
    {
        return $_SESSION[$key] ?? null;
    }

    /**
     * Nastaví hodnotu do session. Pokud sezení zatím nezačalo, bude zinicializováno.
     *
     * @param string $key klíč hodnoty
     * @param mixed $value hodnota
     */
    public function set(string $key, mixed $value): void
    {
        if (!$this->initialized) {
            session_start();
            $this->initialized = true;
        }
        $_SESSION[$key] = $value;
    }

    /**
     * Odebere hodnotu ze session. Pokud sezení zatím nezačalo, bude zinicializováno.
     *
     * @param string $key klíč hodnoty
     */
    public function delete(string $key): void
    {
        if (!$this->initialized) {
            session_start();
            $this->initialized = true;
        }
        unset($_SESSION[$key]);
    }

    /**
     * Metoda promaže session. Session musí být nejprve zinicializována konstruktorem nebo metodami set či delete.
     */
    public function clear(): void
    {
        if ($this->initialized) {
            session_unset();
        }
    }
}
