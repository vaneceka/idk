from pathlib import Path

import pytest

from checks.word.header_footer.second_section_header_text_check import (
    SecondSectionHeaderHasTextCheck,
)
from tests.utils.load_document import load_document

BASE = Path(__file__).parent


@pytest.mark.parametrize(
    "filename",
    [
        "ok.docx",
        "ok.odt",
    ],
)
def test_second_section_header_has_text_ok(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = SecondSectionHeaderHasTextCheck().run(doc, word_assignment)

    assert result.passed is True
    assert result.points == 0

@pytest.mark.parametrize(
    "filename",
    [
        "ok_link_to_prev.docx",
    ],
)
def test_second_section_header_has_text_link_to_prev_ok(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = SecondSectionHeaderHasTextCheck().run(doc, word_assignment)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize(
    "filename",
    [
        "fail.docx",
        "fail.odt",
    ],
)
def test_second_section_header_has_text_fail(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = SecondSectionHeaderHasTextCheck().run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None
