from pathlib import Path

import pytest

from checks.excel.formatting.table_border_check import TableBorderCheck
from tests.utils.load_document import load_document

BASE = Path(__file__).parent


@pytest.mark.parametrize(
    "filename",
    [
        "ok.xlsx",
        "ok.ods",
    ],
)
def test_table_border_check_ok(filename, excel_assignment):
    doc = load_document(BASE / filename)
    result = TableBorderCheck().run(doc, excel_assignment)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize(
    "filename",
    [
        "fail_bold.xlsx",
        "fail_bold.ods",
    ],
)
def test_table_border_check_bold_fail(filename, excel_assignment):
    doc = load_document(BASE / filename)
    result = TableBorderCheck().run(doc, excel_assignment)

    assert result.passed is False
    assert result.points is None


@pytest.mark.parametrize(
    "filename",
    [
        "fail_inner.xlsx",
        "fail_inner.ods",
    ],
)
def test_table_border_check_inner_fail(filename, excel_assignment):
    doc = load_document(BASE / filename)
    result = TableBorderCheck().run(doc, excel_assignment)

    assert result.passed is False
    assert result.points is None
