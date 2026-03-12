<?php

declare(strict_types=1);

namespace App;

use App\Controller\Admin\AdminController;
use App\Controller\Admin\LogController;
use App\Controller\Admin\LogoutController as AdminLogoutController;
use App\Controller\Admin\OptionsController;
use App\Controller\Admin\ProfilesController;
use App\Controller\Admin\StudentsController;
use App\Controller\Admin\SubjectsController;
use App\Controller\Admin\UsersController;
use App\Controller\AssignmentsController;
use App\Controller\ErrorController;
use App\Controller\HomeController;
use App\Controller\LogoutController;

/**
 * Třída zodpovědná za zvolení správného Controlleru podle cesty v URL adrese.
 *
 * @author Michal Turek
 */
final class Router
{
    /**
     * @var array|string[] Seznam controllerů a jejich rout v aplikaci
     */
    public static array $routes = [
        'home' => HomeController::class,
        'assignments' => AssignmentsController::class,
        'logout' => LogoutController::class,
        'admin' => AdminController::class,
        'admin/logout' => AdminLogoutController::class,
        'admin/users' => UsersController::class,
        'admin/options' => OptionsController::class,
        'admin/subjects' => SubjectsController::class,
        'admin/profiles' => ProfilesController::class,
        'admin/students' => StudentsController::class,
        'admin/log' => LogController::class,
    ];

    /**
     * Metoda zpracovává příchozí požadavek a ihned spouští daný Controller.
     */
    public static function processRequest(): void
    {
        $path = trim(parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH), '/');
        if (BASE_PATH && str_starts_with($path, BASE_PATH)) {
            $path = substr($path, strlen(BASE_PATH));
        }
        $controller = self::$routes[strtolower($path ?: 'home')] ?? ErrorController::class;
        (new $controller)->run();
    }
}