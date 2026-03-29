<?php

declare(strict_types=1);

namespace App\Model;

/**
 * Manager pro přípravu dat CSV exportu do systému STAG.
 *
 * @author Adam Vaněček
 */
class StagExportManager
{
    /**
     * Rozdělí zkratku předmětu na katedru a samotnou zkratku.
     *
     * @param string $shortcut zkratka předmětu
     * @return array pole obsahující katedru a zkratku předmětu
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

    /**
     * Vrátí hlavičku CSV exportu pro STAG.
     *
     * @return array
     */
    public function getSubmittedExportHeader(): array
    {
        return [
            'katedra',
            'zkratka',
            'rok',
            'semestr',
            'os_cislo',
            'jmeno',
            'prijmeni',
            'titul',
            'nesplnene_prerekvizity',
            'zk_typ_hodnoceni',
            'zk_hodnoceni',
            'zk_body',
            'zk_datum',
            'zk_pokus',
            'zk_ucit_idno',
            'zk_jazyk',
            'zk_ucit_jmeno',
        ];
    }

    /**
     * Vrátí hodnocení pro STAG podle stavu zadání.
     *
     * @param AssignmentState|null $state stav studenta
     * @return string
     */
    public function stateToStagGrade(?\App\Model\Database\Types\AssignmentState $state): string
    {
        if ($state === \App\Model\Database\Types\AssignmentState::ACCEPTED) {
            return 'S';
        }

        if ($state === \App\Model\Database\Types\AssignmentState::REJECTED) {
            return 'N';
        }

        return '';
    }

    /**
     * Sestaví jeden řádek CSV exportu pro STAG.
     *
     * @param array $student data studenta
     * @param string $katedra katedra
     * @param string $zkratka zkratka předmětu
     * @param string $rok akademický rok
     * @param string $semestr semestr ve formátu STAG
     * @param string $zkHodnoceni hodnocení
     * @param string $zkDatum datum hodnocení
     * @return array
     */
    public function buildSubmittedExportRow(
        array $student,
        string $katedra,
        string $zkratka,
        string $rok,
        string $semestr,
        string $zkHodnoceni,
        string $zkDatum
    ): array {
        return [
            $katedra,
            $zkratka,
            $rok,
            $semestr,
            (string)$student['student_number'],
            (string)$student['name'],
            (string)$student['surname'],
            '',
            '',
            '',
            $zkHodnoceni,
            '',
            $zkDatum,
            '1',
            '',
            '',
            '',
        ];
    }
}