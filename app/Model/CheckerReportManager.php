<?php

declare(strict_types=1);

namespace App\Model;

/**
 * Třída pro práci s reporty automatické kontroly odevzdaných zadání.
 *
 * @author Adam Vaněček
 */
class CheckerReportManager
{
    /**
     * Vrátí základní adresář pro soubory studenta a zadání.
     *
     * @param int $studentId ID studenta
     * @param int $assignmentId ID zadání
     * @return string cesta k základnímu adresáři
     */
    public function getBaseDir(int $studentId, int $assignmentId): string
    {
        return rtrim(DOCUMENT_FOLDER, '/') . '/' . $studentId . '/' . $assignmentId;
    }

    /**
     * Načte informace o primárním odevzdání ze souboru.
     *
     * @param string $primaryPath cesta k souboru s primárním odevzdáním
     * @return array|null data primárního odevzdání, nebo null pokud soubor neexistuje nebo je neplatný
     */
    public function readPrimary(string $primaryPath): ?array
    {
        if (!is_file($primaryPath)) {
            return null;
        }

        $data = json_decode((string) file_get_contents($primaryPath), true);
        return is_array($data) ? $data : null;
    }

    /**
     * Uloží informace o primárním odevzdání do souboru.
     *
     * @param string $baseDir základní adresář pro soubory
     * @param string $primaryPath cesta k souboru s primárním odevzdáním
     * @param mixed $upload objekt odevzdaného souboru
     * @param int $seenLatestTime čas posledního známého odevzdání
     * @param bool $manual určuje, zda bylo primární odevzdání nastaveno ručně
     * @return void
     */
    public function writePrimary(string $baseDir, string $primaryPath, $upload, int $seenLatestTime, bool $manual = false): void
    {
        if (!is_dir($baseDir)) {
            mkdir($baseDir, 0775, true);
        }

        $payload = [
            'file_id' => (int) $upload->id,
            // 'filename' => (string) $upload->filename,
            // 'time' => $this->timeToTs($upload->time),
            'manual' => $manual,
            'seen_latest_time' => $seenLatestTime,
        ];

        file_put_contents($primaryPath, json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
    }

    /**
     * Určí primární odevzdání ze seznamu nahraných souborů.
     *
     * @param array $uploads seznam odevzdaných souborů
     * @param string $primaryPath cesta k souboru s primárním odevzdáním
     * @return object|null objekt primárního odevzdání, nebo null pokud žádné neexistuje
     */
    public function resolvePrimaryUpload(array $uploads, string $primaryPath): ?object
    {
        if (empty($uploads)) {
            return null;
        }

        $primary = $this->readPrimary($primaryPath);
        if (!$primary) {
            return $uploads[0];
        }

        $primaryId = (int) ($primary['file_id'] ?? 0);
        foreach ($uploads as $u) {
            if ((int) $u->id === $primaryId) {
                return $u;
            }
        }

        return $uploads[0];
    }

    /**
     * Převede časovou hodnotu na timestamp.
     *
     * @param mixed $time časová hodnota
     * @return int čas ve formátu timestamp
     */
    public function timeToTs($time): int
    {
        if ($time instanceof \DateTimeInterface) {
            return $time->getTimestamp();
        }

        if (is_numeric($time)) {
            return (int) $time;
        }

        return 0;
    }

    /**
     * Najde checker report odpovídající konkrétnímu odevzdanému souboru.
     *
     * @param string $baseDir základní adresář pro soubory
     * @param string $uploadFilename název odevzdaného souboru
     * @param mixed $uploadTime čas odevzdání souboru
     * @return string|null cesta k reportu, nebo null pokud nebyl nalezen
     */
    public function findReportForUpload(string $baseDir, string $uploadFilename, $uploadTime): ?string
    {
        $stem = pathinfo($uploadFilename, PATHINFO_FILENAME);
        $ts = date('YmdHis', $this->timeToTs($uploadTime));

        $pattern = $baseDir . '/*_odevzdani_' . $ts . '_*' . $stem . '.json';
        $hits = glob($pattern) ?: [];

        if ($hits) {
            usort($hits, fn($a, $b) => filemtime($b) <=> filemtime($a));
            return $hits[0];
        }

        $exact = $baseDir . '/' . $stem . '.json';
        return is_file($exact) ? $exact : null;
    }

    /**
     * Načte checker report ze souboru.
     *
     * @param string|null $reportPath cesta k checker reportu
     * @return array|null data checker reportu, nebo null pokud soubor neexistuje nebo je neplatný
     */
    public function loadCheckerReport(?string $reportPath): ?array
    {
        if (!$reportPath || !is_file($reportPath)) {
            return null;
        }

        $data = json_decode((string) file_get_contents($reportPath), true);
        return is_array($data) ? $data : null;
    }

    /**
     * Zajistí, že primární odevzdání odpovídá nejnovějšímu dostupnému souboru.
     *
     * @param string $baseDir základní adresář pro soubory
     * @param string $primaryPath cesta k souboru s primárním odevzdáním
     * @param object|null $latestUpload nejnovější odevzdaný soubor
     * @param int $latestTime čas nejnovějšího odevzdání
     * @return void
     */
    public function ensurePrimaryIsFresh(string $baseDir, string $primaryPath, ?object $latestUpload, int $latestTime): void
    {
        if (!$latestUpload) {
            return;
        }

        $cur = $this->readPrimary($primaryPath);

        if ($cur === null) {
            $this->writePrimary($baseDir, $primaryPath, $latestUpload, $latestTime, false);
            return;
        }

        $seenLatest = (int) ($cur['seen_latest_time'] ?? 0);

        if ($latestTime > $seenLatest) {
            $this->writePrimary($baseDir, $primaryPath, $latestUpload, $latestTime, false);
        }
    }

    /**
     * Vytvoří návrh komentáře na základě checker reportu.
     *
     * @param array|null $checkerReport data checker reportu
     * @return string navržený komentář k hodnocení
     */
    public function buildSuggestedComment(?array $checkerReport): string
    {
        if (!is_array($checkerReport) || !isset($checkerReport['entries']) || !is_array($checkerReport['entries'])) {
            return '';
        }

        $lines = [];
        $lines[] = 'Penalizace: ' . ($checkerReport['total_penalty'] ?? 0);
        $lines[] = '';

        foreach ($checkerReport['entries'] as $e) {
            $passed = (bool) ($e['passed'] ?? false);
            $ignored = (bool) ($e['ignored'] ?? false);
            if ($passed || $ignored) {
                continue;
            }

            $code = (string) ($e['code'] ?? '');
            $name = (string) ($e['name'] ?? '');
            $points = (int) ($e['points'] ?? 0);
            $msg = trim((string) ($e['message'] ?? ''));

            $lines[] = "{$code} – {$name} ({$points})";
            if ($msg !== '') {
                $lines[] = $msg;
            }
            $lines[] = '';
        }

        return trim(implode("\n", $lines));
    }

    /**
     * Sestaví přehled penalizací pro jednotlivá odevzdání.
     *
     * @param string $baseDir základní adresář pro soubory
     * @param array $uploads seznam odevzdaných souborů
     * @return array mapa penalizací podle ID odevzdání
     */
    public function buildUploadPenalties(string $baseDir, array $uploads): array
    {
        $penalties = [];

        foreach ($uploads as $u) {
            $reportPath = $this->findReportForUpload($baseDir, $u->filename, $u->time);

            if ($reportPath && is_file($reportPath)) {
                $data = json_decode((string) file_get_contents($reportPath), true);
                $penalties[$u->id] = is_array($data) ? (int) ($data['total_penalty'] ?? 0) : null;
            } else {
                $penalties[$u->id] = null;
            }
        }

        return $penalties;
    }

    /**
     * Uloží nastavení ignorovaných checker chyb do reportu a přepočítá penalizaci.
     *
     * @param string $reportPath cesta k checker reportu
     * @param array $ignorePost data z formuláře s ignorovanými chybami
     * @return bool true, pokud se operace podařila, jinak false
     */
    public function applyCheckerIgnoresToReport(string $reportPath, array $ignorePost): bool
    {
        if (!$reportPath || !is_file($reportPath)) {
            return false;
        }

        $data = json_decode((string) file_get_contents($reportPath), true);
        if (!is_array($data) || !isset($data['entries']) || !is_array($data['entries'])) {
            return false;
        }

        $ignore = $ignorePost['ignore'] ?? [];
        if (!is_array($ignore)) {
            $ignore = [];
        }

        foreach ($data['entries'] as &$entry) {
            $code = $entry['code'] ?? null;
            if (!$code) {
                continue;
            }
            $entry['ignored'] = array_key_exists($code, $ignore);
        }
        unset($entry);

        $total = 0;
        foreach ($data['entries'] as $entry) {
            $passed = (bool) ($entry['passed'] ?? false);
            $ignored = (bool) ($entry['ignored'] ?? false);
            $points = (int) ($entry['points'] ?? 0);

            if (!$passed && !$ignored) {
                $total += $points;
            }
        }

        $data['total_penalty'] = $total;

        file_put_contents($reportPath, json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
        return true;
    }
}