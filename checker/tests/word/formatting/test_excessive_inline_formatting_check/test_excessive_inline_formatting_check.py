from pathlib import Path

import pytest

from checks.word.formatting.excessive_inline_formatting_check import (
    ExcessiveInlineFormattingCheck,
)
from tests.utils.load_document import load_document

BASE = Path(__file__).parent


@pytest.mark.parametrize(
    "filename",
    ["ok.docx", "ok.odt"],
)
def test_excessive_formatting_check_ok(filename, word_assignment):
    doc = load_document(BASE / filename)
    check = ExcessiveInlineFormattingCheck()

    result = check.run(doc, word_assignment)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize(
    "filename",
    ["fail.docx", "fail.odt"],
)
def test_excessive_formatting_check_font_fail(filename, word_assignment):
    doc = load_document(BASE / filename)
    check = ExcessiveInlineFormattingCheck()

    result = check.run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None

