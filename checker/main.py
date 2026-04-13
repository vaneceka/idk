import argparse
from pathlib import Path
import sys

from core.multi_dir_mode import run_multi_dir_mode
from core.student_dir_mode import run_single_dir_mode

def parse_args() -> argparse.Namespace:
    """
    Načte argumenty příkazové řádky.

    Returns:
        Zpracované argumenty programu.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Nástroj pro kontrolu odevzdaných souborů podle zadaných pravidel."
        ),
        epilog=(
            "Příklad použití: "
            "python main.py --submissions submissions "
            "--assignments assignments --output both"
        ),
    )

    parser.add_argument(
        "--submissions",
        required=False,
        metavar="CESTA",
        help="Cesta ke kořenovému adresáři s odevzdanými pracemi."
    )

    parser.add_argument(
        "--assignments",
        required=False,
        metavar="CESTA",
        help="Cesta ke kořenovému adresáři se zadáními."
    )

    parser.add_argument(
        "--output",
        choices=["console", "txt", "json", "both"],
        default="console",
        metavar="FORMAT",
        help=(
            "Formát výstupu: "
            "console = výpis do konzole, "
            "txt = textový report, "
            "json = JSON report, "
            "both = txt i json."
        ),
    )

    parser.add_argument(
        "--student-dir",
        required=False,
        metavar="CESTA",
        help=(
            "Cesta ke studentské složce nebo k nadřazenému adresáři, "
            "který obsahuje jednu či více studentských složek se souborem assignment.json."
        )
    )

    parser.add_argument(
        "--out-dir",
        required=False,
        metavar="CESTA",
        help="Cesta do výstupní složky, kam se uloží reporty.",
    )

    parser.add_argument(
        "--report-all",
        action="store_true",
        help="Zahrnout do reportu i úspěšné kontroly, nejen nalezené problémy.",
    )

    parser.add_argument(
        "--checks-config",
        required=False,
        default=None,
        metavar="SOUBOR",
        help="Cesta ke konfiguračnímu JSON souboru kontrol. Pokud není zadána, použije se výchozí sada kontrol."
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.student_dir:
        student_path = Path(args.student_dir)
        if not student_path.exists():
            print(f"CHYBA: Zadaná cesta '{args.student_dir}' neexistuje.", file=sys.stderr)
            sys.exit(1)
            
        run_single_dir_mode(args)
        return

    if args.submissions:
        submissions_path = Path(args.submissions)
        if not submissions_path.exists():
            print(f"CHYBA: Zadaná cesta k odevzdáním '{args.submissions}' neexistuje.", file=sys.stderr)
            sys.exit(1)

    if args.assignments:
        assignments_path = Path(args.assignments)
        if not assignments_path.exists():
            print(f"CHYBA: Zadaná cesta k zadáním '{args.assignments}' neexistuje.", file=sys.stderr)
            sys.exit(1)

    run_multi_dir_mode(args)


if __name__ == "__main__":
    main()