<?php

namespace App\Model\GeneratorSuppliers;

/**
 * Třída pro poskytování náhodných témat do úvodního oddílu.
 *
 * @author Michal Turek
 */
class TopicSupplier
{
    /**
     * Témata načtená při prvním náhodném výběru ze souboru.
     *
     * @var string[]
     */
    private array $topics;

    public function __construct(private readonly int $profileId)
    {
    }

    /**
     * Vrátí náhodné téma
     *
     * @return string náhodné téma
     */
    public function getTitle(): string
    {
        if (!isset($this->topics)) {
            if (file_exists(DOCUMENT_FOLDER . '/texts/' . $this->profileId . '/topic.txt')) {
                $this->topics = array_filter(file(DOCUMENT_FOLDER . '/texts/' . $this->profileId . '/topic.txt', FILE_IGNORE_NEW_LINES));
            } else {
                $this->topics = array_filter(file(ROOT_DIR . '/texts/topic.txt', FILE_IGNORE_NEW_LINES));
            }
        }

        return $this->topics[array_rand($this->topics)];
    }
}