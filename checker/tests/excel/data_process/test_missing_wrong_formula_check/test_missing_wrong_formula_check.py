from pathlib import Path

import pytest

from checks.excel.data_process.missing_wrong_formula_check import (
    MissingOrWrongFormulaOrNotCalculatedCheck,
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
def test_missing_wrong_formula_check_ok(filename, excel_assignment):
    doc = load_document(BASE / filename)
    result = MissingOrWrongFormulaOrNotCalculatedCheck().run(doc, excel_assignment)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize(
    "filename",
    [
        "ok_diff_formula.xlsx",
        "ok_diff_formula.ods",
    ],
)
def test_missing_wrong_formula_check_diff_formula_ok(filename, excel_assignment):
    doc = load_document(BASE / filename)
    result = MissingOrWrongFormulaOrNotCalculatedCheck().run(doc, excel_assignment)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize(
    "filename",
    [
        "fail.xlsx",
        "fail.ods",
    ],
)
def test_missing_wrong_formula_check_fail(filename, excel_assignment):
    doc = load_document(BASE / filename)
    result = MissingOrWrongFormulaOrNotCalculatedCheck().run(doc, excel_assignment)

    assert result.passed is False
    assert result.points is None
