from pathlib import Path

from core.report import Report


def save_report_for_base(report: Report, base_path: Path, output_mode: str) -> None:
    """
    Uloží report podle zvoleného výstupního formátu.

    Args:
        report: Report k uložení.
        base_path: Základ cesty bez přípony.
        output_mode: Požadovaný formát výstupu.
    """
    if output_mode in ("txt", "both"):
        report.save_txt(base_path.with_suffix(".txt"))
    if output_mode in ("json", "both"):
        report.save_json(base_path.with_suffix(".json"))

def save_report_next_to_submission(
    report: Report, submission_path: Path, output_mode: str
) -> None:
    """
    Uloží report vedle odevzdaného souboru.

    Args:
        report: Report k uložení.
        submission_path: Cesta k odevzdanému souboru.
        output_mode: Požadovaný formát výstupu.
    """
    base = submission_path.with_suffix("")

    if output_mode in ("txt", "both"):
        report.save_txt(base.with_suffix(".txt"))

    if output_mode in ("json", "both"):
        report.save_json(base.with_suffix(".json"))
