# Systém pro podporu tvorby individuálních zadání

## Instalace

Aplikaci lze provozovat v připraveném prostředí Docker. 

* Vytvořte složky document a temp, umožněte alespoň uživateli www-data (UID 33) do těchto složek zapisovat.
* Ve složce config zkopírujte soubor conf.inc.php.template a pojmenujte jej conf.inc.php. 
  Hodnoty změňte podle potřeby. 
  Přihlašovací údaje k databázi je nutné změnit i v souboru docker-compose.yml.
* Spusťte docker příkazem `docker compose up -d`.
* V rámci kontejneru php-fpm spusťte tyto příkazy (například pomocí `docker compose exec php-fpm bash`):
    * `composer install`
    * `php bin/installDatabase.php`
    * `php bin/createAdminUser.php` - Interaktivní příkaz pro vytvoření účtu administrátora
* Aplikace je přístupná na portu nastaveném v souboru docker-compose.yml, ve výchozím nastavení 8080.
* Před použitím aplikace je nutné se přihlásit do aplikace jako administrátor 
  a nastavit akademický rok a aktuální semestr.