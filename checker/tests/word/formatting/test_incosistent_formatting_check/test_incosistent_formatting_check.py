from pathlib import Path

import pytest

from checks.word.formatting.incosistent_formatting_check import (
    InconsistentFormattingCheck,
)
from tests.utils.load_document import load_document

BASE = Path(__file__).parent


@pytest.mark.parametrize(
    "filename",
    ["ok.docx", "ok.odt"],
)
def test_inconsistent_formatting_check_ok(filename, word_assignment):
    doc = load_document(BASE / filename)
    check = InconsistentFormattingCheck()

    result = check.run(doc, word_assignment)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize(
    "filename",
    ["fail.docx", "fail.odt"],
)
def test_inconsistent_formatting_check_fail(filename, word_assignment):
    doc = load_document(BASE / filename)
    check = InconsistentFormattingCheck()

    result = check.run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None

@pytest.mark.parametrize(
    "filename",
    ["ok2.docx"],
)
def test_inconsistent_formatting_check2_ok(filename, word_assignment):
    doc = load_document(BASE / filename)
    check = InconsistentFormattingCheck()

    result = check.run(doc, word_assignment)

    assert result.passed is True
    assert result.points == 0



@pytest.mark.parametrize(
    "filename",
    ["fail_font_heading.docx", "fail_font_heading.odt"],
)
def test_excessive_formatting_check_font_heading_fail(filename, word_assignment):
    doc = load_document(BASE / filename)
    check = InconsistentFormattingCheck()

    result = check.run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None

@pytest.mark.parametrize(
    "filename",
    ["fail_font_text.docx", "fail_font_text.odt"],
)
def test_excessive_formatting_check_font_text_fail(filename, word_assignment):
    doc = load_document(BASE / filename)
    check = InconsistentFormattingCheck()

    result = check.run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None

@pytest.mark.parametrize(
    "filename",
    ["fail_size.docx", "fail_size.odt"],
)
def test_excessive_formatting_check_size_fail(filename, word_assignment):
    doc = load_document(BASE / filename)
    check = InconsistentFormattingCheck()

    result = check.run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None