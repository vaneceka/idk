

import csv
from pathlib import Path
import shutil

from core.report import Report
from core.report_io import save_report_next_to_submission
from core.submission_finder import find_submission_for_student
from core.submission_pipeline import run_pipeline_for_submission
from core.submission_utils import submission_date_ddmmyyyy

FAIL_THRESHOLD_PENALTY = -70

def find_single_csv(root: Path) -> Path | None:
    """
    Najde jediný CSV soubor ve složce.

    Args:
        root: Kořenová složka.

    Returns:
        Cestu k CSV souboru nebo None.
    """
    csv_files = [
        p for p in root.iterdir() if p.is_file() and p.suffix.lower() == ".csv"
    ]

    if len(csv_files) != 1:
        print(f"Očekáváno 1 CSV v {root}, nalezeno {len(csv_files)}")
        return None

    csv_path = csv_files[0]
    if not csv_path:
        print("Nebylo nalezeno žádné csv")
        return None

    return csv_path

def load_csv_rows(csv_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """
    Načte hlavičku a řádky z CSV souboru.

    Args:
        csv_path: Cesta k CSV souboru.

    Returns:
        Seznam názvů sloupců a seznam řádků.
    """
    encodings = ["utf-8-sig", "utf-8", "cp1250", "iso-8859-2"]

    last_error = None

    for encoding in encodings:
        try:
            with open(csv_path, "r", encoding=encoding, newline="") as f:
                reader = csv.DictReader(f, delimiter=";")
                fieldnames = list(reader.fieldnames or [])
                rows = list(reader)
                return fieldnames, rows
        except UnicodeDecodeError as e:
            last_error = e

    raise UnicodeDecodeError(
        last_error.encoding if last_error else "unknown",
        last_error.object if last_error else b"",
        last_error.start if last_error else 0,
        last_error.end if last_error else 0,
        last_error.reason if last_error else f"Nepodařilo se načíst CSV: {csv_path}",
    )

def validate_required_csv_columns(fieldnames: list[str]) -> bool:
    """
    Ověří přítomnost povinných sloupců v CSV.

    Args:
        fieldnames: Názvy sloupců v CSV.

    Returns:
        True pokud jsou všechny povinné sloupce přítomné, jinak False.
    """
    col_os = "Osobni cislo"
    col_grade = "Hodnoceni"
    col_grade_date = "Hodnoceni-datum"

    if col_os not in fieldnames:
        print(f"CSV nemá sloupec {col_os}. Sloupce: {fieldnames}")
        return False

    if col_grade not in fieldnames:
        print(f"CSV nemá sloupec {col_grade}. Sloupce: {fieldnames}")
        return False

    if col_grade_date not in fieldnames:
        print(f"CSV nemá sloupec {col_grade_date}. Sloupce: {fieldnames}")
        return False

    return True

def csv_note(report: Report) -> str:
    """
    Vrátí stručnou poznámku do CSV z neúspěšných kontrol.

    Args:
        report: Hotový report se záznamy kontrol.

    Returns:
        Stručný text vhodný do sloupce Hodnoceni-poznamka.
    """
    parts: list[str] = []

    for item in report.entries:
        result = item.result
        if getattr(result, "passed", False):
            continue

        message = str(getattr(result, "message", "")).strip()
        first_line = message.splitlines()[0] if message else ""

        if first_line:
            parts.append(f"{item.code}: {first_line}")
        else:
            parts.append(item.code)

    return " | ".join(parts)

def decide_S_or_N(total_penalty: int) -> str:
    """
    Určí výsledné hodnocení podle penalizace.

    Args:
        total_penalty: Celková bodová penalizace.

    Returns:
        'S' nebo 'N'.
    """
    return "N" if total_penalty <= FAIL_THRESHOLD_PENALTY else "S"

def process_csv_row(
    row: dict[str, str],
    *,
    root: Path,
    assignments_root: Path | None,
    output: str,
    include_passed: bool,
    checks_config_path: str | None,
) -> None:
    """
    Zpracuje jeden řádek CSV se studentem.

    Args:
        row: Jeden řádek CSV.
        root: Kořenová složka s odevzdáními.
        assignments_root: Kořenová složka se zadáními.
        output: Požadovaný výstupní formát.
        include_passed: Zda zahrnout i úspěšné kontroly.
        checks_config_path: Cesta ke konfiguraci kontrol.
    """
    col_os = "Osobni cislo"
    col_grade = "Hodnoceni"
    col_grade_date = "Hodnoceni-datum"
    col_note = "Hodnoceni-poznamka"

    os_cislo = (row.get(col_os) or "").strip()
    if not os_cislo:
        return

    submission = find_submission_for_student(root, os_cislo)
    if not submission:
        return

    report, _office_path, tmp_dir = run_pipeline_for_submission(
        submission,
        assignments_root=assignments_root,
        include_passed=include_passed,
        checks_config_path=checks_config_path,
    )

    try:
        total_penalty = report._compute_total_penalty()

        if output in ("txt", "json", "both"):
            save_report_next_to_submission(report, submission, output)

        row[col_grade] = decide_S_or_N(total_penalty)
        row[col_grade_date] = submission_date_ddmmyyyy(submission)

        if col_note in row:
            row[col_note] = csv_note(report)
    finally:
        if tmp_dir is not None:
            shutil.rmtree(tmp_dir, ignore_errors=True)

