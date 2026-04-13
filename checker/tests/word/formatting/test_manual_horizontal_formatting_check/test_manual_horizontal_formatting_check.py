from pathlib import Path

import pytest

from checks.word.formatting.manual_horizontal_formatting_check import (
    ManualHorizontalSpacingCheck,
)
from tests.utils.load_document import load_document

BASE = Path(__file__).parent


@pytest.mark.parametrize(
    "filename",
    ["ok.docx", "ok.odt"],
)
def test_manual_horizontal_spacing_ok(filename, word_assignment):
    doc = load_document(BASE / filename)
    check = ManualHorizontalSpacingCheck()

    result = check.run(doc, word_assignment)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize(
    "filename",
    ["fail.docx", "fail.odt"],
)
def test_manual_horizontal_spacing_fail(filename, word_assignment):
    doc = load_document(BASE / filename)
    check = ManualHorizontalSpacingCheck()

    result = check.run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None
