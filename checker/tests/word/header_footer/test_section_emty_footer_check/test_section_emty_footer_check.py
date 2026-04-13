from pathlib import Path

import pytest

from checks.word.header_footer.section_emty_footer_check import SectionFooterEmptyCheck
from tests.utils.load_document import load_document

BASE = Path(__file__).parent


@pytest.mark.parametrize(
    "filename, section_number",
    [
        ("ok.docx", 1),
        ("ok.odt", 1),
    ],
)
def test_section_footer_empty_ok(filename, section_number, word_assignment):
    doc = load_document(BASE / filename)

    check = SectionFooterEmptyCheck(section_number)
    result = check.run(doc, word_assignment)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize(
    "filename, section_number",
    [
        ("fail.docx", 1),
        ("fail.odt", 1),
    ],
)
def test_section_footer_empty_fail(filename, section_number, word_assignment):
    doc = load_document(BASE / filename)

    check = SectionFooterEmptyCheck(section_number)
    result = check.run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None
