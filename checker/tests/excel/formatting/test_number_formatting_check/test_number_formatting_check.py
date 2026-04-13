from pathlib import Path

import pytest

from checks.excel.formatting.number_formatting_check import NumberFormattingCheck
from tests.utils.load_document import load_document

BASE = Path(__file__).parent


@pytest.mark.parametrize(
    "filename",
    [
        "ok.xlsx",
        "ok.ods",
    ],
)
def test_number_formatting_check_ok(filename, excel_assignment):
    doc = load_document(BASE / filename)
    result = NumberFormattingCheck().run(doc, excel_assignment)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize(
    "filename",
    [
        "fail.xlsx",
        "fail.ods",
    ],
)
def test_number_formatting_check_fail(filename, excel_assignment):
    doc = load_document(BASE / filename)
    result = NumberFormattingCheck().run(doc, excel_assignment)

    assert result.passed is False
    assert result.points is None
