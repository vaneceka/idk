<?php

declare(strict_types=1);

namespace App\Controller;

use App\Model\Database\DatabaseManager;
use App\Model\Session;
use App\Router;
use App\Utils\Alert;
use Twig\Environment;
use Twig\Loader\FilesystemLoader;
use Twig\TwigFunction;

/**
 * Obecná třída Controlleru, od které dědí všechny ostatní Controllery.
 * Má na starosti základní činnost, jako je příprava šablon, vytváření managerů pro práci s databází
 * a session apod.
 *
 * @author Michal Turek
 */
abstract class Controller
{
    /**
     * Třída pro obsluhu databáze
     *
     * @var DatabaseManager|null
     */
    private ?DatabaseManager $database = null;
    /**
     * Třída pro práci se session
     *
     * @var Session|null
     */
    private ?Session $session = null;
    /**
     * Pole obsahující proměnné, které jsou vloženy do šablony.
     *
     * @var array<string, mixed>
     */
    protected array $templateData = [];
    /**
     * Pole obsahující stavové zprávy, které budou zaslány do view.
     *
     * @var Alert[]
     */
    private array $alertMessages = [];
    /**
     * Atribut může obsahovat název twig souboru s konkrétní šablonou.
     * Pokud není definován, dojde k automatickému nalezení správného souboru.
     *
     * @var string
     */
    private string $template;

    /**
     * Metoda, která zpracovává příchozí požadavek.
     * Je implementována v konkrétních Controllerech.
     */
    protected abstract function process(): void;

    /**
     * Metoda, která zpracovává příchozí požadavek.
     * Během svého běhu zavolá metodu {@see static::process()},
     * která provede konkrétní zpracování uživatelova požadavku.
     */
    public function run(): void
    {
        $this->templateData['currentUrl'] = $_SERVER['REQUEST_URI'];
        $this->templateData['basePath'] = BASE_PATH;

        /* Zpracování stavových zpráv uložených v session. */
        if ($alerts = $this->getSession()->get(Session::ALERTS)) {
            $this->alertMessages = $alerts;
            $this->getSession()->delete(Session::ALERTS);
        }

        /* Zavolání obslužné metody konkrétního controlleru. */
        $this->process();

        /* Připravení Twigu */
        $loader = new FilesystemLoader(ROOT_DIR . '/templates');
        $twig = new Environment($loader, [
            'cache' => ROOT_DIR . '/temp/twig_cache',
            'debug' => true,
        ]);
        $twig->addFunction(new TwigFunction('createLink', $this->createLink(...)));
        $twig->addFunction(new TwigFunction('isLinkCurrent', fn (string $controller): bool => str_ends_with($this::class, '\\' . ucfirst($controller) . 'Controller')));

        $this->templateData['alertMessages'] = $this->alertMessages;

        /* Nalezení a vyrenderování správného view */
        $rendered = $twig->render('pages/' . ($this->template ?? $this->getTemplateName()), $this->templateData);

        echo $rendered;
    }

    /**
     * Metoda nalezne soubor s šablonou podle jména daného Controlleru.
     * Soubor s šablonou je oproti jménu Controlleru vždy pojmenován malým počátečním písmenem a neobsahuje slovo Controller.
     * Pokud je Controller umístěn v podbalíku, musí být v podsložce umístěn i soubor s šablonou.
     *
     * @return string relativní cesta k souboru ve složce templates/pages/
     */
    private function getTemplateName(): string
    {
        $classNameParts = explode('\\', substr($this::class, strlen('App\\Controller\\')));
        $classNameParts = array_map(fn (string $part): string => lcfirst(str_replace('Controller', '', $part)), $classNameParts);
        return implode('/', $classNameParts) . '.twig';
    }

    /**
     * Metoda podle zadaných parametrů sestaví odkaz na konkrétní stránku v aplikaci.
     *
     * @param string $controller cesta, pro kterou je {@see Router} schopen nalézt Controller.
     * @param array|null $data další parametry přenášené v URL
     * @return string sestavený odkaz
     */
    public final function createLink(string $controller, ?array $data = null): string {
        if ($controller === 'home') {
            return (!empty($data) ? '/' . BASE_PATH . '?' . http_build_query($data) : '/' . BASE_PATH);
        } else {
            return '/' . BASE_PATH  . $controller . (!empty($data) ? '?' . http_build_query($data) : '');
        }
    }

    /**
     * Metoda přidá novou stavovou zprávu, která bude vypsána v šabloně.
     * Pokud by došlo k redirectu, uloží se stavová zpráva do session, odkud se vyjme při příštím požadavku.
     *
     * @param string $class css třída, podle které se stavová zpráva zabarví (např. success nebo danger)
     * @param string $message zpráva
     */
    protected final function alertMessage(string $class, string $message): void
    {
        $this->alertMessages[] = new Alert($message, $class);
    }

    /**
     * Metoda provede přesměrování do jiné části aplikace a ukončí zpracovávání aktuálního požadavku.
     *
     * @param string $controller cesta, pro kterou je {@see Router} schopen nalézt Controller.
     * @param array|null $data další parametry přenášené v URL
     */
    protected final function redirect(string $controller, ?array $data = null): never
    {
        if ($this->alertMessages) {
            $this->getSession()->set(Session::ALERTS, $this->alertMessages);
        }

        header('Location: ' . $this->createLink($controller, $data));
        exit();
    }

    /**
     * Metoda nastaví HTTP kód odpovědi na 404 Nenalezeno a změní šablonu na Error.twig.
     */
    protected final function error404(): void
    {
        http_response_code(404);
        $this->template = 'error.twig';
    }

    /**
     * Metoda vrátí třídu pro práci s databázi.
     * Při prvním volání dojde k inicializaci této třídy.
     *
     * @return DatabaseManager manažer pro práci s databází
     */
    protected final function getDatabase(): DatabaseManager
    {
        if (!$this->database) {
            $this->database = new DatabaseManager();
        }
        return $this->database;
    }

    /**
     * Metoda vrátí třídu pro práci se session.
     * Při prvním volání dojde k inicializaci této třídy.
     *
     * @return Session třída pro práci se session
     */
    protected final function getSession(): Session
    {
        if (!$this->session) {
            $this->session = new Session();
        }
        return $this->session;
    }
}
