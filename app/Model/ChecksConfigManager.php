<?php

declare(strict_types=1);

namespace App\Model;

class ChecksConfigManager
{
    
    /**
     * Načte definice kontrol daného typu z registry JSON souboru.
     *
     * @param string $type typ kontrol
     * @return array seznam definic kontrol daného typu
     * @author Adam Vaněček
     */
    public function getAllCheckDefinitions(string $type): array
    {   
        
        // $registryPath = CHECKER_REGISTRY;
        $registryPath = '/checker/checks/checks_config/checks_registry.json';

        if (!is_file($registryPath)) {
            return [];
        }

        $data = json_decode((string) file_get_contents($registryPath), true);
        if (!is_array($data)) {
            return [];
        }

        $items = $data[$type] ?? null;
        if (!is_array($items)) {
            return [];
        }

        $out = [];
        foreach ($items as $row) {
            if (!is_array($row)) continue;

            $code = isset($row['code']) && is_string($row['code']) ? trim($row['code']) : '';
            if ($code === '') continue;

            $out[] = [
                'code' => $code,
                'title' => isset($row['title']) && is_string($row['title']) ? $row['title'] : '',
                'default_enabled' => array_key_exists('default_enabled', $row) ? (bool)$row['default_enabled'] : true,
                'order' => array_key_exists('order', $row) ? (int)$row['order'] : 0,
            ];
        }

        return $out;
    }

    /**
     * Vytvoří mapu výchozího povolení kontrol podle jejich definic.
     *
     * @param array $definitions seznam definic kontrol
     * @return array mapa ve tvaru ['KOD' => true/false]
     */
    public function buildDefaultMap(array $definitions): array
    {
        $map = [];

        foreach ($definitions as $definition) {
            $code = isset($definition['code']) && is_string($definition['code'])
                ? trim($definition['code'])
                : '';

            if ($code === '') {
                continue;
            }

            $map[$code] = (bool)($definition['default_enabled'] ?? true);
        }

        return $map;
    }

    /**
     * Očistí mapu povolených kontrol podle výchozí mapy.
     *
     * @param mixed $raw vstupní mapa hodnot
     * @param array $defaultMap výchozí mapa kontrol
     * @return array výsledná mapa povolených kontrol
     */
    public function sanitizeEnabledMap($raw, array $defaultMap): array
    {
        $out = $defaultMap;

        if (!is_array($raw)) {
            return $out;
        }

        foreach ($raw as $k => $v) {
            if (!is_string($k) || !is_bool($v)) {
                continue;
            }

            $k = trim($k);
            if ($k === '') {
                continue;
            }

            if (!array_key_exists($k, $out)) {
                continue;
            }

            $out[$k] = $v;
        }

        return $out;
    }

    /**
     * Ověří, že sekce konfigurace má tvar asociativního pole s boolean hodnotami.
     *
     * @param mixed $raw vstupní data sekce konfigurace
     * @return array|null ověřená sekce konfigurace, nebo null při neplatném formátu
     */
    public function assertConfigSectionIsMap($raw): ?array
    {
        if (!is_array($raw)) {
            return null;
        }

        $keys = array_keys($raw);
        $isList = ($keys === range(0, count($keys) - 1));
        if ($isList) {
            return null;
        }

        foreach ($raw as $k => $v) {
            if (!is_string($k) || !is_bool($v)) {
                return null;
            }
        }

        return $raw;
    }

    /**
     * Vrátí normalizovanou konfiguraci kontrol včetně student_view.
     *
     * @param array|null $dbCfg konfigurace z databáze
     * @param array $defaultTextMap výchozí mapa textových kontrol
     * @param array $defaultSheetMap výchozí mapa tabulkových kontrol
     * @return array normalizovaná konfigurace
     */
    public function buildResolvedConfig(
        ?array $dbCfg,
        array $defaultTextMap,
        array $defaultSheetMap
    ): array {
        $dbCfg ??= [];

        $textMap = $this->sanitizeEnabledMap($dbCfg['text'] ?? null, $defaultTextMap);
        $sheetMap = $this->sanitizeEnabledMap($dbCfg['spreadsheet'] ?? null, $defaultSheetMap);

        $studentViewCfg = is_array($dbCfg['student_view'] ?? null) ? $dbCfg['student_view'] : [];

        return [
            'text' => $textMap,
            'spreadsheet' => $sheetMap,
            'student_view' => [
                'enabled' => (bool)($studentViewCfg['enabled'] ?? false),
                'min_penalty' => abs((int)($studentViewCfg['min_penalty'] ?? 100)),
            ],
        ];
    }

    /**
     * Připraví seznam kontrol pro šablonu.
     *
     * @param array $definitions definice kontrol
     * @param array $enabledMap mapa povolených kontrol
     * @return array seznam kontrol pro výpis
     */
    public function buildChecksList(array $definitions, array $enabledMap): array
    {
        $checks = [];

        foreach ($definitions as $definition) {
            $code = $definition['code'];
            $checks[] = [
                'code' => $code,
                'title' => $definition['title'] ?? '',
                'enabled' => (bool)($enabledMap[$code] ?? false),
            ];
        }

        return $checks;
    }

    /**
     * Připraví data pro obrazovku konfigurace kontrol.
     *
     * @param array $textDefs definice textových kontrol
     * @param array $sheetDefs definice tabulkových kontrol
     * @param array|null $dbCfg konfigurace z databáze
     * @return array data pro šablonu
     */
    public function buildChecksConfigViewData(
        array $textDefs,
        array $sheetDefs,
        ?array $dbCfg
    ): array {
        $defaultTextMap = $this->buildDefaultMap($textDefs);
        $defaultSheetMap = $this->buildDefaultMap($sheetDefs);

        $resolved = $this->buildResolvedConfig($dbCfg, $defaultTextMap, $defaultSheetMap);

        return [
            'defaultTextMap' => $defaultTextMap,
            'defaultSheetMap' => $defaultSheetMap,
            'textChecks' => $this->buildChecksList($textDefs, $resolved['text']),
            'sheetChecks' => $this->buildChecksList($sheetDefs, $resolved['spreadsheet']),
            'studentViewEnabled' => $resolved['student_view']['enabled'],
            'studentViewMinPenalty' => $resolved['student_view']['min_penalty'],
        ];
    }

    /**
     * Zpracuje uploadnutou JSON konfiguraci.
     *
     * @param array $data dekódovaný JSON
     * @param array $defaultTextMap výchozí mapa textových kontrol
     * @param array $defaultSheetMap výchozí mapa tabulkových kontrol
     * @return array normalizovaná data pro uložení
     * @throws \InvalidArgumentException při neplatném formátu
     */
    public function parseUploadedConfig(
        array $data,
        array $defaultTextMap,
        array $defaultSheetMap
    ): array {
        if (!array_key_exists('text', $data) || !array_key_exists('spreadsheet', $data)) {
            throw new \InvalidArgumentException('JSON musí obsahovat klíče "text" a "spreadsheet".');
        }

        $textRaw = $this->assertConfigSectionIsMap($data['text']);
        $sheetRaw = $this->assertConfigSectionIsMap($data['spreadsheet']);

        if ($textRaw === null || $sheetRaw === null) {
            throw new \InvalidArgumentException(
                'JSON musí mít formát mapy: "text": { "T_...": true/false } a "spreadsheet": { "S_...": true/false }.'
            );
        }

        $textMap = $this->sanitizeEnabledMap($textRaw, $defaultTextMap);
        $sheetMap = $this->sanitizeEnabledMap($sheetRaw, $defaultSheetMap);

        $studentViewRaw = is_array($data['student_view'] ?? null) ? $data['student_view'] : [];

        $studentViewEnabled = (bool)($studentViewRaw['enabled'] ?? false);

        $studentViewMinPenalty = -100;
        if (isset($studentViewRaw['min_penalty']) && is_numeric($studentViewRaw['min_penalty'])) {
            $studentViewMinPenalty = (int)$studentViewRaw['min_penalty'];
        }

        return [
            'text' => $textMap,
            'spreadsheet' => $sheetMap,
            'student_view_enabled' => $studentViewEnabled,
            'student_view_min_penalty' => $studentViewMinPenalty,
        ];
    }

    /**
     * Zpracuje odeslanou konfiguraci z formuláře.
     *
     * @param array $post odeslaná data formuláře
     * @param array $defaultTextMap výchozí mapa textových kontrol
     * @param array $defaultSheetMap výchozí mapa tabulkových kontrol
     * @return array normalizovaná data pro uložení
     */
    public function parsePostedConfig(
        array $post,
        array $defaultTextMap,
        array $defaultSheetMap
    ): array {
        $textPost = $post['text'] ?? [];
        $sheetPost = $post['spreadsheet'] ?? [];

        if (!is_array($textPost)) {
            $textPost = [];
        }

        if (!is_array($sheetPost)) {
            $sheetPost = [];
        }

        $textMap = $defaultTextMap;
        $sheetMap = $defaultSheetMap;

        foreach ($textMap as $code => $_) {
            $textMap[$code] = isset($textPost[$code]) && (string)$textPost[$code] === '1';
        }

        foreach ($sheetMap as $code => $_) {
            $sheetMap[$code] = isset($sheetPost[$code]) && (string)$sheetPost[$code] === '1';
        }

        $studentViewEnabled = isset($post['student_view_enabled']) && (string)$post['student_view_enabled'] === '1';

        $studentViewMinPenalty = -100;
        if (isset($post['student_view_min_penalty']) && is_numeric($post['student_view_min_penalty'])) {
            $studentViewMinPenalty = (int)$post['student_view_min_penalty'];
        }

        return [
            'text' => $textMap,
            'spreadsheet' => $sheetMap,
            'student_view_enabled' => $studentViewEnabled,
            'student_view_min_penalty' => $studentViewMinPenalty,
        ];
    }

}