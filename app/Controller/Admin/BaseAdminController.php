<?php

declare(strict_types=1);

namespace App\Controller\Admin;

use App\Controller\Controller;
use App\Model\Database\Entities\User;
use App\Model\Session;

/**
 * Společný předek pro všechny Controllery pro admin sekci.
 * Zajišťuje kontrolu přihlášení uživatele a případně provede přesměrování na přihlašovací stránku.
 *
 * @author Michal Turek
 */
abstract class BaseAdminController extends Controller
{
    protected ?User $loggedUser;

    public function run(): void
    {
        $adminUserId = $this->getSession()->get(Session::ADMIN);
        if (!$adminUserId && !($this instanceof AdminController)) {
            $this->alertMessage('danger', 'Nejste přihlášen');
            $this->redirect('admin');
        }

        if ($adminUserId) {
            $adminUser = $this->getDatabase()->getAdminUserById($adminUserId);
            if (!$adminUser) {
                $this->alertMessage('danger', 'Neplatný uživatel');
                $this->getSession()->delete(Session::ADMIN);
                $this->redirect('admin');
            }

            $this->templateData['loggedUser'] = $this->loggedUser = $adminUser;
        } else {
            $this->templateData['loggedUser'] = $this->loggedUser = null;
        }

        parent::run();
    }
}