from pathlib import Path
from types import SimpleNamespace

import pytest

from checks.excel.general.wrong_submitted_spreadsheet_file_check import (
    WrongSubmittedSpreadsheetFileCheck,
)
from tests.utils.load_document import load_document

BASE = Path(__file__).parent


@pytest.mark.parametrize(
    "filename",
    [
        "ok.xlsx",
        "ok.ods",
    ],
)
def test_wrong_submitting_file_check_ok(filename, excel_assignment):
    doc = load_document(BASE / filename)
    result = WrongSubmittedSpreadsheetFileCheck().run(doc, excel_assignment)

    assert result.passed is True
    assert result.points == 0


BASE = Path(__file__).parent


@pytest.mark.parametrize("filename", ["fail.xsx", "fail.od"])
def test_wrong_submitting_file_check_fail(filename, excel_assignment):
    path = BASE / filename
    doc = SimpleNamespace(path=str(path))

    result = WrongSubmittedSpreadsheetFileCheck().run(doc, excel_assignment)

    assert result.passed is False
