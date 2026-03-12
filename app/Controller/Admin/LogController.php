<?php

declare(strict_types=1);

namespace App\Controller\Admin;

use App\Model\Database\Types\LogType;

/**
 * Controller sloužící pro zobrazení záznamu aktivit studentů i vyučujících v aplikaci.
 * Zobrazený výpis je možné filtrovat pomocí uživatele, typu záznamu nebo textu v daném záznamu.
 *
 * @author Michal Turek
 */
class LogController extends BaseAdminController
{
    protected function process(): void
    {
        if (!$this->loggedUser->isAdmin) {
            $this->error404();
            return;
        }

        $page = 1;
        if (isset($_GET['pageNum']) && is_numeric($_GET['pageNum'])) {
            $page = (int) $_GET['pageNum'];
        }

        $search = null;
        $searchType = null;
        $searchUser = null;
        if (isset($_GET['search']) && is_string($_GET['search'])) {
            $search = $_GET['search'];
        }
        if (isset($_GET['searchUser']) && is_string($_GET['searchUser'])) {
            $searchUser = $_GET['searchUser'];
        }
        if (isset($_GET['searchType']) && is_numeric($_GET['searchType'])) {
            $searchType = LogType::tryFrom((int) $_GET['searchType']);
        }

        $this->templateData['limit'] = 20;
        $this->templateData['page'] = $page;
        $this->templateData['logCount'] = $this->getDatabase()->getLogCount(searchUser: $searchUser, searchText: $search, searchType: $searchType);
        $this->templateData['logs'] = $this->getDatabase()->getLogs($page, 20, searchUser: $searchUser, searchText: $search, searchType: $searchType);
        $this->templateData['search'] = $search;
        $this->templateData['searchType'] = $searchType;
        $this->templateData['searchUser'] = $searchUser;
        $this->templateData['logTypes'] = LogType::cases();
    }
}
