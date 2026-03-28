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
     * @author Adam Vaněček
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
     * @author Adam Vaněček
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
     * @author Adam Vaněček
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
}