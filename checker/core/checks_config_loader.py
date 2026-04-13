from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ChecksConfig:
    """
    Uchovává nastavení zapnutých a vypnutých kontrol pro textové a tabulkové dokumenty.
    """

    text: dict[str, bool]
    spreadsheet: dict[str, bool]


def load_checks_config(path: str | Path) -> ChecksConfig:
    """
    Načte konfiguraci kontrol z JSON souboru.

    Args:
        path: Cesta ke konfiguračnímu souboru.

    Returns:
        Objekt ChecksConfig s nastavením textových a tabulkových kontrol.

    Raises:
        ValueError: Pokud sekce 'text' nebo 'spreadsheet' nemá formát dict[str, bool].
    """
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))

    text = data.get("text") or {}
    sheet = data.get("spreadsheet") or {}

    if not isinstance(text, dict) or not all(
        isinstance(k, str) and isinstance(v, bool) for k, v in text.items()
    ):
        raise ValueError(f"{p}: 'text' musí být dict[str, bool]")
    if not isinstance(sheet, dict) or not all(
        isinstance(k, str) and isinstance(v, bool) for k, v in sheet.items()
    ):
        raise ValueError(f"{p}: 'spreadsheet' musí být dict[str, bool]")

    text = {k.strip(): v for k, v in text.items() if k.strip()}
    sheet = {k.strip(): v for k, v in sheet.items() if k.strip()}

    return ChecksConfig(text=text, spreadsheet=sheet)
