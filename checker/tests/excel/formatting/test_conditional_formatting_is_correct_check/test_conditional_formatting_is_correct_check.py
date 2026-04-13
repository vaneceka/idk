from pathlib import Path

import pytest

from checks.excel.formatting.conditional_formatting_is_correct_check import (
    ConditionalFormattingCorrectnessCheck,
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
def test_conditional_formatting_is_correct_check_ok(filename, excel_assignment):
    doc = load_document(BASE / filename)
    result = ConditionalFormattingCorrectnessCheck().run(doc, excel_assignment)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize(
    "filename",
    [
        "fail_range.xlsx",
        "fail_range.ods",
    ],
)
def test_conditional_formatting_is_correct_check_invalid_range_fail(
    filename, excel_assignment
):
    doc = load_document(BASE / filename)
    result = ConditionalFormattingCorrectnessCheck().run(doc, excel_assignment)

    assert result.passed is False
    assert result.points is None


@pytest.mark.parametrize(
    "filename",
    [
        "fail_condition.xlsx",
        "fail_condition.ods",
    ],
)
def test_conditional_formatting_is_correct_check_invalid_condition_fail(
    filename, excel_assignment
):
    doc = load_document(BASE / filename)
    result = ConditionalFormattingCorrectnessCheck().run(doc, excel_assignment)

    assert result.passed is False
    assert result.points is None
