from dataclasses import dataclass
from pathlib import Path

from checks.base_check import CheckResult


@dataclass
class ReportEntry:
    """
    Představuje jednu položku reportu s kódem kontroly a jejím výsledkem.

    Attributes:
        code: Kód provedené kontroly.
        result: Výsledek dané kontroly.
    """

    code: str
    result: CheckResult


@dataclass
class ResolvedSubmission:
    """
    Uchovává informace o připraveném odevzdaném souboru po jeho zpracování.

    Attributes:
        office_path: Cesta k výslednému kancelářskému souboru.
        kind: Typ rozpoznaného souboru nebo dokumentu.
        tmp_dir: Dočasný adresář použitý při zpracování.
        error: Chybová zpráva, pokud zpracování selhalo.
    """

    office_path: Path | None
    kind: str | None
    tmp_dir: Path | None
    error: str | None
