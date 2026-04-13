from pathlib import Path

import pytest

from assignment.spreadsheet.spreadsheet_assignment_loader import (
    load_spreadsheet_assignment,
)
from assignment.text.text_assignment_loader import load_text_assignment

ROOT = Path(__file__).parent
ASSIGNMENTS = ROOT / "assignments"


@pytest.fixture(scope="session")
def word_assignment():
    return load_text_assignment(ASSIGNMENTS / "word_assignment.json")


@pytest.fixture(scope="session")
def excel_assignment():
    return load_spreadsheet_assignment(ASSIGNMENTS / "excel_assignment.json")
