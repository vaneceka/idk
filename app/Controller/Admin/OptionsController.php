<?php

declare(strict_types=1);

namespace App\Controller\Admin;

use App\Model\Database\Types\LogType;
use App\Model\Database\Types\Options;

/**
 * Controller sloužící k nastavování systémových proměnných.
 *
 * @author Michal Turek
 */
class OptionsController extends BaseAdminController
{
    protected function process(): void
    {
        if (!$this->loggedUser->isAdmin) {
            $this->error404();
            return;
        }

        if (isset($_POST['admin_edit_options_form'])) {
            $this->processEditOptions();
        } else {
            $this->templateData['post'] = [
                'year' => $this->getDatabase()->getOption(Options::YEAR),
                'semester' => $this->getDatabase()->getOption(Options::SEMESTER),
            ];
        }
    }

    // FORMULÁŘE

    /**
     * Metoda provede zpracování formuláře pro nastavení systémových proměnných.
     */
    private function processEditOptions(): void
    {
        $post = [];

        $missing = false;

        if (isset($_POST['year'])) {
            $post['year'] = $_POST['year'];
        } else {
            $missing = true;
        }

        if (isset($_POST['semester'])) {
            $post['semester'] = $_POST['semester'];
        } else {
            $missing = true;
        }

        $this->templateData['post'] = $post;

        if ($missing) {
            $this->alertMessage('danger', 'Nejsou vyplněna všechna požadovaná pole');
            return;
        }

        $this->getDatabase()->setOption(Options::YEAR, $post['year']);
        $this->getDatabase()->setOption(Options::SEMESTER, $post['semester']);

        $this->getDatabase()->log('Upraveno nastavení systému (rok: ' . $post['year'] . ', semestr: ' . ($post['semester'] == '1' ? 'letní': 'zimní') . ')', LogType::OPTIONS, userId: $this->loggedUser->id);
        $this->alertMessage('success', 'Nastavení systému upraveno');
        $this->redirect('admin/options');
    }
}
