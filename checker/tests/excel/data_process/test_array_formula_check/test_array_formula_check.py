from pathlib import Path

import pytest

from checks.excel.data_process.array_formula_check import ArrayFormulaCheck
from tests.utils.load_document import load_document

BASE = Path(__file__).parent


@pytest.mark.parametrize(
    "filename",
    [
        "ok.xlsx",
        "ok.ods",
    ],
)
def test_array_formula_ok(filename, excel_assignment):
    doc = load_document(BASE / filename)
    result = ArrayFormulaCheck().run(doc, excel_assignment)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize("filename", ["fail_array.xlsx", "fail_array.ods"])
def test_array_formula_fail(filename, excel_assignment):
    doc = load_document(BASE / filename)
    result = ArrayFormulaCheck().run(doc, excel_assignment)

    assert result.passed is False
    assert result.points is None
