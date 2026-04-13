from pathlib import Path
import re

from core.submission_utils import score_submission_file

ATTEMPT_DIR_RE = re.compile(r"^pokus[_-]?(\d+)$", re.IGNORECASE)

GENERATED_FILENAMES = {
    "assignment.json",
    "primary.json",
    "automaticka_kontrola.log",
    ".DS_Store",
}

IGNORED_SUFFIXES = {
    ".log",
}

GENERATED_REPORT_SUFFIXES = {
    ".txt",
    ".json",
}


def _is_submission_candidate(path: Path) -> bool:
    """
    Vrátí, zda soubor může být považován za odevzdání.

    Args:
        path: Cesta k souboru.

    Returns:
        True, pokud soubor splňuje podmínky pro zpracování, jinak False.
    """
    if not path.is_file():
        return False

    if path.name.startswith("~$"):
        return False

    if path.name.startswith("."):
        return False

    if path.name in GENERATED_FILENAMES:
        return False

    if path.suffix.lower() in IGNORED_SUFFIXES:
        return False

    return True


def _filter_generated_report_files(files: list[Path]) -> list[Path]:
    """
    Odstraní reporty, pokud existuje původní soubor se stejným názvem.

    Args:
        files: Seznam nalezených souborů.

    Returns:
        Seznam souborů bez nadbytečných vygenerovaných reportů.
    """
    real_basenames: set[str] = set()

    for p in files:
        if p.suffix.lower() not in GENERATED_REPORT_SUFFIXES:
            real_basenames.add(p.stem)

    filtered: list[Path] = []
    for p in files:
        if p.suffix.lower() in GENERATED_REPORT_SUFFIXES and p.stem in real_basenames:
            continue
        filtered.append(p)

    return filtered


def find_latest_office_file(
    dir_path: Path, student_id: str | None = None
) -> Path | None:
    """
    Najde nejnovější soubor ve složce.

    Args:
        dir_path: Složka, ve které se hledá.
        student_id: Volitelné omezení na ID studenta.

    Returns:
        Cestu k nejnovějšímu souboru nebo None.
    """
    candidates: list[Path] = []

    for f in dir_path.iterdir():
        if not _is_submission_candidate(f):
            continue
        if student_id is not None and student_id not in f.name:
            continue

        candidates.append(f)

    candidates = _filter_generated_report_files(candidates)
    return max(candidates, key=score_submission_file) if candidates else None


def find_assignment_folder(
    assignments_root: Path, submitted_file: Path
) -> Path | None:
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


def find_latest_submission_in_dir(dir_path: Path) -> Path | None:
    """
    Najde nejnovější soubor ve složce.

    Args:
        dir_path: Složka, ve které se má hledat.

    Returns:
        Cestu k vybranému souboru nebo None.
    """
    candidates: list[Path] = []

    for p in dir_path.rglob("*"):
        if not _is_submission_candidate(p):
            continue

        candidates.append(p)

    candidates = _filter_generated_report_files(candidates)
    return max(candidates, key=score_submission_file) if candidates else None


def find_submission_for_student(root: Path, os_cislo: str) -> Path | None:
    """
    Najde odevzdání pro zadané osobní číslo.

    Logika:
    - pokud existují podsložky typu pokus_01, pokus_02, ..., vezme se nejvyšší pokus
    - z vybraného pokusu se vezme nejnovější soubor
    - pokud pokus_* složky neexistují, hledá se v celé studentské složce

    Args:
        root: Kořenová složka s odevzdáními.
        os_cislo: Osobní číslo studenta.

    Returns:
        Cestu k nalezenému souboru nebo None.
    """
    os_cislo = os_cislo.strip()
    if not os_cislo:
        return None

    student_dirs: list[Path] = []
    for d in root.rglob("*"):
        if d.is_dir() and os_cislo in d.name:
            student_dirs.append(d)

    if not student_dirs:
        return None

    student_dir = min(student_dirs, key=lambda p: len(p.parts))

    attempt_dirs: list[tuple[int, Path]] = []
    for child in student_dir.iterdir():
        if not child.is_dir():
            continue

        m = ATTEMPT_DIR_RE.match(child.name)
        if not m:
            continue

        attempt_number = int(m.group(1))
        attempt_dirs.append((attempt_number, child))

    if attempt_dirs:
        latest_attempt_dir = max(attempt_dirs, key=lambda x: x[0])[1]
        return find_latest_submission_in_dir(latest_attempt_dir)

    return find_latest_submission_in_dir(student_dir)