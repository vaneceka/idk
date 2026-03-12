<?php

namespace App\Model\GeneratorSuppliers;

use App\Generator\TextDocument\PointList;

/**
 * Třída pro poskytování náhodných seznamů.
 *
 * @author Michal Turek
 */
class ListSupplier
{
    /**
     * Seznamy načtené z json souboru při prvním náhodném výběru.
     *
     * @var array<string, string[]>
     */
    private array $points;

    public function __construct(private readonly int $profileId)
    {
    }

    /**
     * Vrátí náhodný dvouúrovňový seznam
     *
     * @param bool $ordered zda-li má být seznam číslovaný nebo nečíslovaný
     * @return PointList objekt představující seznam
     */
    public function getList(bool $ordered): PointList
    {
        if (!isset($this->points)) {
            if (file_exists(DOCUMENT_FOLDER . '/texts/' . $this->profileId . '/list.json')) {
                $this->points = json_decode(file_get_contents(DOCUMENT_FOLDER . '/texts/' . $this->profileId . '/list.json'), true);
            } else {
                $this->points = json_decode(file_get_contents(ROOT_DIR . '/texts/list.json'), true);
            }
        }

        $randomKeys = array_rand($this->points, rand(3, 5));

        $collection = [];
        foreach ($randomKeys as $key) {
            $collection[$key] = $this->points[$key];
        }
        return new PointList($ordered, $collection);
    }
}