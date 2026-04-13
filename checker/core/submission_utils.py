from __future__ import annotations

import zipfile
from datetime import datetime as DateTime
from pathlib import Path
import re


SUBMIT_TS_RE = re.compile(r"odevzdani_(\d{14})", re.IGNORECASE)

def is_zip(path: Path) -> bool:
    """
    Ověří, zda je soubor platný ZIP archiv.

    Args:
        path: Cesta k souboru.

    Returns:
        True pokud je soubor ZIP, jinak False.
    """
    try:
        with zipfile.ZipFile(path):
            return True
    except zipfile.BadZipFile:
        return False
    except Exception:
        return False

def find_assignment_folder(assignments_root: Path, submitted_file: Path) -> Path | None:
    """
    Najde složku assignmentu odpovídající odevzdanému souboru.

    Args:
        assignments_root: Kořenová složka se zadáními.
        submitted_file: Odevzdaný soubor.

    Returns:
        Složku assignmentu nebo None.
    """
    for folder in assignments_root.rglob("*"):
        if not folder.is_dir():
            continue

        assignment = folder / "assignment.json"
        if not assignment.exists():
            continue

        if (folder / submitted_file.name).is_file():
            return folder

    return None

def score_submission_file(p: Path) -> tuple[int, int]:
    """
    Vypočítá skóre souboru pro výběr nejnovějšího odevzdání.

    Args:
        p: Cesta k souboru.

    Returns:
        Dvojici hodnot použitou pro porovnání souborů.
    """
    m = SUBMIT_TS_RE.search(p.name)
    if m:
        return (2, int(m.group(1)))
    return (1, int(p.stat().st_mtime))

def submission_date_ddmmyyyy(path: Path) -> str:
    """
    Vrátí datum odevzdání ve formátu DD.MM.RRRR.

    Args:
        path: Cesta k souboru.

    Returns:
        Datum odevzdání jako text.
    """
    m = SUBMIT_TS_RE.search(path.name)
    if m:
        ts = m.group(1)
        dt = DateTime.strptime(ts, "%Y%m%d%H%M%S")
        return dt.strftime("%d.%m.%Y")

    dt = DateTime.fromtimestamp(path.stat().st_mtime)
    return dt.strftime("%d.%m.%Y")