import argparse
from pathlib import Path
import shutil

from core.report_io import save_report_for_base
from core.submission_finder import find_latest_office_file
from core.submission_pipeline import run_pipeline_for_submission


def _resolve_dirs_to_process(student_dir: Path) -> list[Path]:
    """
    Vrátí složky určené ke zpracování.

    Args:
        student_dir: Vstupní studentská složka.

    Returns:
        Seznam složek ke zpracování.
    """
    if (student_dir / "assignment.json").exists():
        return [student_dir]

    return sorted(
        {p.parent for p in student_dir.rglob("assignment.json") if p.is_file()}
    )

def _process_single_student_dir(
    one_student_dir: Path,
    *,
    output: str,
    out_dir: Path | None,
    include_passed: bool,
    checks_config_path: str | None,
) -> None:
    """
    Zpracuje jednu studentskou složku.

    Args:
        one_student_dir: Složka jednoho studenta.
        output: Požadovaný výstupní formát.
        out_dir: Výstupní složka.
        include_passed: Zda zahrnout i úspěšné kontroly.
        checks_config_path: Cesta ke konfiguraci kontrol.
    """
    print(f"[START] {one_student_dir}")

    target_out_dir = out_dir if out_dir is not None else one_student_dir
    target_out_dir.mkdir(parents=True, exist_ok=True)

    assignment_path = one_student_dir / "assignment.json"
    latest = find_latest_office_file(one_student_dir)
    print(f"[FILE] {latest}")

    if not latest:
        print(f"Ve složce {one_student_dir} nebyl nalezen žádný office soubor.")
        return

    report, office_path, tmp_dir = run_pipeline_for_submission(
        latest,
        assignment_path=assignment_path,
        include_passed=include_passed,
        checks_config_path=checks_config_path,
    )
    print(f"[DONE] {one_student_dir}")

    try:
        if output == "console":
            print(f"\n=== {one_student_dir.name} ===")
            report.print()
        else:
            report_source = office_path if office_path is not None else latest
            base = target_out_dir / report_source.stem
            save_report_for_base(report, base, output)
    finally:
        if tmp_dir is not None:
            shutil.rmtree(tmp_dir, ignore_errors=True)

def run_single_dir_mode(args: argparse.Namespace) -> None:
    """
    Spustí režim zpracování jedné složky.

    Args:
        args: Argumenty příkazové řádky.
    """
    student_dir = Path(args.student_dir)

    if not student_dir.exists() or not student_dir.is_dir():
        print(f"Složka neexistuje nebo není adresář: {student_dir}")
        return

    dirs_to_process = _resolve_dirs_to_process(student_dir)
    if not dirs_to_process:
        print(
            f"V {student_dir} chybí assignment.json a nebyl nalezen ani v přímých podsložkách."
        )
        return

    out_dir = Path(args.out_dir) if args.out_dir else None

    for one_student_dir in dirs_to_process:
        _process_single_student_dir(
            one_student_dir,
            output=args.output,
            out_dir=out_dir,
            include_passed=args.report_all,
            checks_config_path=args.checks_config,
        )
