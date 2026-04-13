from pathlib import Path

import pytest

from checks.word.structure.chapter3_numbering_continuity_check import (
    ThirdSectionPageNumberingContinuesCheck,
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
def test_chapter3_page_number_continuity_ok(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = ThirdSectionPageNumberingContinuesCheck().run(doc, word_assignment)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize(
    "filename",
    [
        "fail_missing_page_num.docx",
        "fail_missing_page_num.odt",
        "fail_page_num_restart.docx",
        "fail_page_num_restart.odt",
    ],
)
def test_chapter3_page_number_continuity_fail(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = ThirdSectionPageNumberingContinuesCheck().run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None
