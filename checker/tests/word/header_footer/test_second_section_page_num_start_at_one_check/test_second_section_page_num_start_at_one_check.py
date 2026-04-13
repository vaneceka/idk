from pathlib import Path

import pytest

from checks.word.header_footer.second_section_page_num_start_at_one_check import (
    SecondSectionPageNumberStartsAtOneCheck,
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
def test_second_section_page_number_start_at_one_text_ok(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = SecondSectionPageNumberStartsAtOneCheck().run(doc, word_assignment)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize(
    "filename",
    [
        "fail.docx",
        "fail.odt",
    ],
)
def test_second_section_page_number_start_at_one_text_file(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = SecondSectionPageNumberStartsAtOneCheck().run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None
