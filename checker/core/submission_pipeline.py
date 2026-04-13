import json
from pathlib import Path
import shutil
import tempfile
from typing import Any
import zipfile

from assignment.spreadsheet.spreadsheet_assignment_loader import load_spreadsheet_assignment
from assignment.text.text_assignment_loader import load_text_assignment
from checks.base_check import CheckResult
from checks.checks_all import build_excel_checks, build_word_checks
from checks.excel.general.wrong_submitted_spreadsheet_file_check import WrongSubmittedSpreadsheetFileCheck
from checks.word.general.wrong_submitted_text_file_check import WrongSubmittedTextFileCheck
from core.checks_config_loader import load_checks_config
from core.report import Report
from core.runner import Runner
from core.submission_utils import find_assignment_folder, is_zip
from documents.spreadsheet.spreadsheet_document import SpreadsheetDocument
from documents.text.text_document import TextDocument
from models.core_models import ResolvedSubmission

OFFICE_SUFFIXES = {".docx", ".odt", ".xlsx", ".ods"}

def run_pipeline_for_submission(
    submission_path: Path,
    *,
    assignments_root: Path | None = None,
    assignment_path: Path | None = None,
    include_passed: bool = False,
    checks_config_path: str | None = None,
) -> tuple[Report, Path | None, Path | None]:
    """
    Spustí kontrolní pipeline nad jedním odevzdáním.

    Args:
        submission_path: Cesta k odevzdanému souboru.
        assignments_root: Kořenová složka se zadáními.
        assignment_path: Přímá cesta k assignment.json.
        include_passed: Zda zahrnout i úspěšné kontroly.
        checks_config_path: Cesta ke konfiguraci kontrol.

    Returns:
        Report, cestu ke zpracovanému office souboru a případnou dočasnou složku.
    """
    report = Report(include_passed)
    print(f"[PIPELINE START] {submission_path}")

    resolved = _resolve_submission(submission_path)
    print(f"[RESOLVED] office_path={resolved.office_path}, error={resolved.error}")

    if resolved.error:
        report.add("T_X05", CheckResult(False, resolved.error, None))
        return report, None, resolved.tmp_dir

    office_path = resolved.office_path
    assert office_path is not None

    if assignment_path is None and assignments_root is not None:
        folder = find_assignment_folder(assignments_root, office_path)
        if not folder:
            report.add(
                "SYSTEM",
                CheckResult(
                    False, f"Nenalezen assignment pro {office_path.name}", None
                ),
            )
            return report, office_path, resolved.tmp_dir

        assignment_path = folder / "assignment.json"

    ctx = {
        "submitted_path": str(office_path),
        "checks_config_path": checks_config_path,
    }

    if assignment_path is not None:
        ctx["assignment_dir"] = str(assignment_path.parent)

    print(f"[PROCESS FILE] {office_path}")
    report = process_one_office_file(
        office_path,
        assignment_path,
        include_passed=include_passed,
        context=ctx,
    )

    return report, office_path, resolved.tmp_dir

def _expected_kind_from_assignment(assignment_path: Path) -> str | None:
    """
    Určí očekávaný typ souboru podle assignmentu.

    Args:
        assignment_path: Cesta k assignment.json.

    Returns:
        'text', 'spreadsheet' nebo None.
    """
    with open(assignment_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "cells" in data:
        return "spreadsheet"

    if "styles" in data or "headlines" in data:
        return "text"

    return None

def _resolve_submission(submission: Path) -> ResolvedSubmission:
    """
    Připraví odevzdaný soubor ke zpracování.

    Args:
        submission: Cesta k odevzdanému souboru.

    Returns:
        Informace o nalezeném office souboru, jeho typu a případné chybě.
    """
    suf = submission.suffix.lower()

    if suf in OFFICE_SUFFIXES:
        kind = _classify_office_file(submission)

        if kind is None:
            return ResolvedSubmission(
                None, None, None, f"Nesprávný typ souboru: {submission.name}"
            )
        return ResolvedSubmission(submission, kind, None, None)

    if suf != ".zip":
        return ResolvedSubmission(
            None, None, None, f"Nepodporovaný soubor: {submission.name}"
        )

    tmp_dir = Path(tempfile.mkdtemp(prefix="sub_"))

    try:
        with zipfile.ZipFile(submission) as zf:
            zf.extractall(tmp_dir)

        office_files: list[Path] = []
        for f in tmp_dir.rglob("*"):
            if not f.is_file():
                continue
            if f.name.startswith("~$"):
                continue
            if f.suffix.lower() not in OFFICE_SUFFIXES:
                continue
            if not is_zip(f):
                continue
            office_files.append(f)

        if not office_files:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            return ResolvedSubmission(
                None, None, None, f"ZIP neobsahuje office soubor: {submission.name}"
            )

        if len(office_files) > 1:
            names = ", ".join(sorted(p.name for p in office_files))
            shutil.rmtree(tmp_dir, ignore_errors=True)
            return ResolvedSubmission(
                None,
                None,
                None,
                f"ZIP obsahuje více office souborů ({len(office_files)}): {names}",
            )

        original_office_path = office_files[0]

        new_name = submission.with_suffix('').name
        if not new_name.lower().endswith(original_office_path.suffix.lower()):
            new_name += original_office_path.suffix

        office_path = original_office_path.parent / new_name
        original_office_path.rename(office_path)

        kind = _classify_office_file(office_path)
        if kind is None:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            return ResolvedSubmission(
                None,
                None,
                None,
                f"Soubor v ZIPu není text ani spreadsheet: {office_path.name}",
            )

        return ResolvedSubmission(office_path, kind, tmp_dir, None)

    except zipfile.BadZipFile:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return ResolvedSubmission(None, None, None, f"Poškozený ZIP: {submission.name}")
    except Exception as e:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return ResolvedSubmission(
            None, None, None, f"Chyba při rozbalení ZIP: {submission.name} ({e})"
        )

def _classify_office_file(path: Path) -> str | None:
    """
    Určí typ office souboru.

    Args:
        path: Cesta k souboru.

    Returns:
        'text', 'spreadsheet' nebo None.
    """
    if WrongSubmittedTextFileCheck().run_on_path(path).passed:
        return "text"
    if WrongSubmittedSpreadsheetFileCheck().run_on_path(path).passed:
        return "spreadsheet"
    return None

def _safe_open_text(path: Path, report: Report) -> TextDocument | None:
    """
    Bezpečně otevře textový dokument.

    Args:
        path: Cesta k souboru.
        report: Report pro záznam případné chyby.

    Returns:
        Otevřený dokument nebo None.
    """
    chk = WrongSubmittedTextFileCheck()
    pre = chk.run_on_path(path)

    if not pre.passed:
        report.add(chk.code, pre)
        return None

    try:
        doc = TextDocument.from_path(path)
        report.add(chk.code, pre)
        return doc
    except Exception as e:
        report.add(
            chk.code,
            CheckResult(
                False, f"Soubor nelze otevřít jako Word/Writer: {path.name} ({e})", None
            ),
        )
        return None

def _safe_open_spreadsheet(path: Path, report: Report) -> SpreadsheetDocument | None:
    """
    Bezpečně otevře tabulkový dokument.

    Args:
        path: Cesta k souboru.
        report: Report pro záznam případné chyby.

    Returns:
        Otevřený dokument nebo None.
    """
    chk = WrongSubmittedSpreadsheetFileCheck()
    pre = chk.run_on_path(path)

    if not pre.passed:
        report.add(chk.code, pre)
        return None

    try:
        doc = SpreadsheetDocument.from_path(str(path))
        report.add(chk.code, pre)
        return doc
    except Exception as e:
        report.add(
            chk.code,
            CheckResult(
                False, f"Soubor nelze otevřít jako Excel/Calc: {path.name} ({e})", None
            ),
        )
        return None

def process_one_office_file(
    office_path: Path,
    assignment_path: Path | None,
    *,
    include_passed: bool = False,
    context: dict[str, Any] | None = None,
) -> Report:
    report = Report(include_passed)

    kind = _classify_office_file(office_path)

    expected_kind = None
    if assignment_path is not None:
        expected_kind = _expected_kind_from_assignment(assignment_path)

    if expected_kind is not None and kind != expected_kind:
        expected_label = (
            "textový dokument" if expected_kind == "text" else "tabulkový soubor"
        )
        actual_label = "textový dokument" if kind == "text" else "tabulkový soubor"

        report.add(
            "T_X05",
            CheckResult(
                False,
                f"Odevzdán nesprávný typ souboru. Zadání vyžaduje {expected_label}, ale byl odevzdán {actual_label}.",
                None,
            ),
        )
        return report

    print(f"[PROCESS START] {office_path}")
    print(f"[KIND] {kind}")

    if kind is None:
        report.add(
            "T_X05",
            CheckResult(False, f"Odevzdán nesprávný soubor: {office_path.name}", None),
        )
        return report

    ctx = context or {}
    ctx.setdefault("submitted_path", str(office_path))
    if assignment_path is not None:
        ctx.setdefault("assignment_dir", str(assignment_path.parent))

    word_cfg = None
    excel_cfg = None

    cfg_path = ctx.get("checks_config_path")
    if cfg_path:
        try:
            cfg = load_checks_config(cfg_path)
            word_cfg = cfg.text
            excel_cfg = cfg.spreadsheet
        except Exception as e:
            report.add(
                "SYSTEM",
                CheckResult(False, f"Nelze načíst checks config ({cfg_path}): {e}", None),
            )

    if kind == "text":
        doc = _safe_open_text(office_path, report)
        if doc is None:
            return report

        text_assignment = (
            load_text_assignment(str(assignment_path))
            if assignment_path is not None
            else None
        )

        runner = Runner(build_word_checks(word_cfg))
        for check, result in runner.run(doc, text_assignment, ctx):
            report.add(check.code, result)

        return report

    sheet = _safe_open_spreadsheet(office_path, report)
    if sheet is None:
        return report

    spreadsheet_assignment = (
        load_spreadsheet_assignment(str(assignment_path))
        if assignment_path is not None
        else None
    )

    runner = Runner(build_excel_checks(excel_cfg))
    for check, result in runner.run(sheet, spreadsheet_assignment, ctx):
        report.add(check.code, result)

    return report
