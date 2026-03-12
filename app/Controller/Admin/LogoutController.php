<?php

declare(strict_types=1);

namespace App\Controller\Admin;

use App\Model\Database\Types\LogType;
use App\Model\Session;

/**
 * Controller sloužící k odhlášení přihlášeného administrátora.
 * Po odhlášení je přesměrován zpět na {@link AdminController}.
 *
 * @author Michal Turek
 */
class LogoutController extends BaseAdminController
{
    protected function process(): void
    {
        if ($this->loggedUser !== null) {
            $this->getSession()->delete(Session::ADMIN);
            $this->getDatabase()->log('Uživatel se odhlásil', LogType::LOGOUT, userId: $this->loggedUser->id);
            $this->alertMessage('success', 'Úspěšně odhlášeno');
        }
        $this->redirect('admin');
    }
}
