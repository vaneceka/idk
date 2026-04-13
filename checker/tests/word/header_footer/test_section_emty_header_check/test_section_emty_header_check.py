from pathlib import Path

import pytest

from checks.word.header_footer.section_emty_header_check import SectionHeaderEmptyCheck
from tests.utils.load_document import load_document

BASE = Path(__file__).parent


@pytest.mark.parametrize(
    "filename, section_number",
    [
        ("ok.docx", 1),
        ("ok.odt", 1),
        ("ok.docx", 3),
        ("ok.odt", 3),
    ],
)
def test_section_header_empty_ok(filename, section_number, word_assignment):
    doc = load_document(BASE / filename)

    check = SectionHeaderEmptyCheck(section_number)
    result = check.run(doc, word_assignment)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize(
    "filename, section_number",
    [
        ("fail.docx", 1),
        ("fail.odt", 1),
        ("fail.docx", 3),
        ("fail.odt", 3),
    ],
)
def test_section_header_empty_fail(filename, section_number, word_assignment):
    doc = load_document(BASE / filename)

    check = SectionHeaderEmptyCheck(section_number)
    result = check.run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None
