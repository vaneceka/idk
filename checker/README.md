# Automatická kontrola dokumentů

Tato složka obsahuje validační část systému („checker“), která vyhodnocuje odevzdané soubory (DOCX, ODT, XLSX, ODS, podle `assignment.json`, pokud je k dispozici, a volitelné konfigurace kontrol.

Checker lze používat:

- **samostatně z příkazové řádky** pro ruční testování nebo dávkové zpracování,
- **integrovaně z webové aplikace**, kde PHP spouští checker na pozadí.

Níže jsou popsány instalační a spouštěcí skripty pro **Linux/macOS (`.sh`)** i **Windows (`.bat`)**.

## Požadavky

- Python 3.10 nebo novější s podporou `venv`
- `pip`

> Ve variantě s Dockerem se Python a virtuální prostředí typicky vytváří uvnitř kontejneru.  
> Ve variantě bez Dockeru se virtuální prostředí vytváří lokálně ve složce `.venv` v kořenové složce checkeru.

## Instalace závislostí

Přejděte do kořenové složky checkeru nebo projektu, kde se nachází složka `bin`. 
> **Poznámka pro Docker:** Pokud používáte Docker, tento krok zcela odpadá. Prostředí sestavíte příkazem `docker-compose build`.

### Linux / macOS

Spusťte:

```bash
chmod +x bin/install_checker.sh bin/run_checker.sh
bin/install_checker.sh
```

### Windows

Otevřete **PowerShell** nebo **CMD** a spusťte:

```bat
bin\install_checker.bat
```

## Spuštění checkeru

### Linux / macOS

```bash
bin/run_checker.sh [ARGUMENTY]
```

### Windows

```bat
bin\run_checker.bat [ARGUMENTY]
```

## Checker podporuje dva režimy.

### 1) Single-dir režim (`--student-dir`)

Používá se pro zpracování jedné složky nebo stromu složek, kde se nachází odevzdané soubory (DOCX, ODT, XLSX, ODS). 

**Soubor `assignment.json` není k běhu nutný.** - Pokud se ve složce nachází, checker podle něj přizpůsobí pravidla.
- Pokud **chybí**, checker soubory přesto zkontroluje a aplikuje na ně obecnou sadu výchozích kontrol (případně se řídí tím, co mu předáte přes parametr `--checks-config`).

Tento režim lze použít jak pro jednu konkrétní složku studenta, tak pro strukturu stažených prací ze STAGu.
Příklad:

```bash
bin/run_checker.sh \
  --student-dir "/cesta/k/studentovi" \
  --output json \
  --checks-config "/cesta/k/checks_config.json"
```

Parametry:

- `--output` může být `console`, `txt`, `json` nebo `both`
- `--checks-config` je volitelný; pokud není zadán, použije se výchozí sada kontrol
- `--report-all` zahrne do reportu i úspěšné kontroly

### 2) Multi-dir režim (`--submissions` + `--assignments`)

Používá se pro dávkové zpracování balíku prací, například exportovaných z IS/STAG.

Příklad:

```bash
bin/run_checker.sh \
  --submissions "/cesta/k/exportu" \
  --assignments "/cesta/k/assignments" \
  --output both \
  --checks-config "/cesta/k/checks_config.json"
```

Ve `--submissions` se očekává:

- právě jeden CSV soubor
- soubory studentů (office dokumenty nebo ZIP archivy)


## Integrace do webové aplikace (PHP)

Webová aplikace typicky spouští checker pomocí wrapper skriptu `run_checker.sh` nebo `run_checker.bat`, případně ekvivalentním příkazem nad `main.py`.

Používané argumenty bývají zejména:

- `--student-dir`
- `--out-dir`
- `--output`
- `--checks-config`

