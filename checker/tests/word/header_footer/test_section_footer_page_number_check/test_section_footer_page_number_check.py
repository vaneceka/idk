from pathlib import Path

import pytest

from checks.word.header_footer.section_footer_page_number_check import (
    SectionFooterHasPageNumberCheck,
)
from tests.utils.load_document import load_document

BASE = Path(__file__).parent


@pytest.mark.parametrize(
    "filename, section_number",
    [
        ("ok.docx", 2),
        ("ok.odt", 2),
        ("ok.docx", 3),
        ("ok.odt", 3),
    ],
)
def test_footer_has_page_number_ok(filename, section_number, word_assignment):
    doc = load_document(BASE / filename)

    check = SectionFooterHasPageNumberCheck(section_number)
    result = check.run(doc, word_assignment)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize(
    "filename, section_number",
    [
        ("fail.docx", 2),
        ("fail.odt", 2),
        ("fail.docx", 3),
        ("fail.odt", 3),
    ],
)
def test_footer_has_page_number_fail(filename, section_number, word_assignment):
    doc = load_document(BASE / filename)

    check = SectionFooterHasPageNumberCheck(section_number)
    result = check.run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None
