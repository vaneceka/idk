from pathlib import Path

import pytest

from checks.excel.data_process.named_range_usage_check import NamedRangeUsageCheck
from tests.utils.load_document import load_document

BASE = Path(__file__).parent


@pytest.mark.parametrize(
    "filename",
    [
        "ok.xlsx",
        "ok.ods",
    ],
)
def test_named_range_usage_check_ok(filename, excel_assignment):
    doc = load_document(BASE / filename)
    result = NamedRangeUsageCheck().run(doc, excel_assignment)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize(
    "filename",
    [
        "fail.xlsx",
        "fail.ods",
    ],
)
def test_named_range_usage_check_fail(filename, excel_assignment):
    doc = load_document(BASE / filename)
    result = NamedRangeUsageCheck().run(doc, excel_assignment)

    assert result.passed is False
    assert result.points is None
