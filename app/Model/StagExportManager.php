<?php

declare(strict_types=1);

namespace App\Model;

class StagExportManager
{
    /**
     * Rozdělí zkratku předmětu na katedru a samotnou zkratku.
     *
     * @param string $shortcut zkratka předmětu
     * @return array pole obsahující katedru a zkratku předmětu
     * @author Adam Vaněček
     */
    public function splitSubjectShortcut(string $shortcut): array
    {
        $shortcut = trim($shortcut);

        if (str_contains($shortcut, '/')) {
            [$katedra, $zkratka] = array_map('trim', explode('/', $shortcut, 2));
            return [$katedra, $zkratka];
        }

        return [$shortcut, $shortcut];
    }

    /**
     * Převede interní označení semestru na formát používaný ve STAGu.
     *
     * @param string $sem označení semestru
     * @return string semestr ve formátu STAG
     * @author Adam Vaněček
     */
    public function semesterToStag(string $sem): string
    {
        $sem = strtoupper(trim($sem));

        if ($sem === 'W') {
            return 'ZS';
        }

        if ($sem === 'S') {
            return 'LS';
        }

        return 'ZS';
    }
}