
import argparse
import csv
from pathlib import Path

from core.csv_processing import find_single_csv, load_csv_rows, process_csv_row, validate_required_csv_columns



def run_multi_dir_mode(args: argparse.Namespace) -> None:
    """
    Spustí režim zpracování více odevzdání.

    Args:
        args: Argumenty příkazové řádky.
    """
    if not args.submissions:
        print("Chybí --submissions (nebo použij --student-dir).")
        return

    root = Path(args.submissions)
    assignments_root = Path(args.assignments) if args.assignments else None

    csv_path = find_single_csv(root)
    if csv_path is None:
        return

    fieldnames, rows = load_csv_rows(csv_path)
    if not validate_required_csv_columns(fieldnames):
        return

    for row in rows:
        process_csv_row(
            row,
            root=root,
            assignments_root=assignments_root,
            output=args.output,
            include_passed=args.report_all,
            checks_config_path=args.checks_config,
        )
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Hotovo: {csv_path}")