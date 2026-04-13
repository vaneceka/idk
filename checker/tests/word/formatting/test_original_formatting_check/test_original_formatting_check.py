from pathlib import Path

import pytest

from checks.word.formatting.original_formatting_check import OriginalFormattingCheck
from tests.utils.load_document import load_document

BASE = Path(__file__).parent


@pytest.mark.parametrize(
    "filename",
    ["ok.docx", "ok.odt"],
)
def test_original_formatting_ok(filename, word_assignment):
    doc = load_document(BASE / filename)
    check = OriginalFormattingCheck()

    result = check.run(doc, assignment=None)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize(
    "filename",
    ["fail.docx", "fail.odt"],
)
def test_original_formatting_fail(filename, word_assignment):
    doc = load_document(BASE / filename)
    check = OriginalFormattingCheck()

    result = check.run(doc, assignment=None)

    assert result.passed is False
    assert result.points is None
