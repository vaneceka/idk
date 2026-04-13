from pathlib import Path

import pytest

from checks.word.formatting.heading_style_check import HeadingStyleCheck
from tests.utils.load_document import load_document

BASE = Path(__file__).parent


@pytest.mark.parametrize(
    "filename",
    ["ok.docx", "ok.odt"],
)
@pytest.mark.parametrize(
    "level",
    [1, 2, 3],
)
def test_heading_style_ok(filename, level, word_assignment):
    doc = load_document(BASE / filename)
    check = HeadingStyleCheck(level)

    result = check.run(doc, word_assignment)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize(
    "filename",
    ["fail.docx", "fail.odt"],
)
@pytest.mark.parametrize(
    "level",
    [1, 2, 3],
)
def test_heading_style_fail(filename, level, word_assignment):
    doc = load_document(BASE / filename)
    check = HeadingStyleCheck(level)

    result = check.run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None
