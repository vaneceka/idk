from pathlib import Path

import pytest

from checks.word.structure.first_chapter_page1_check import (
    FirstChapterStartsOnPageOneCheck,
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
def test_first_chapter_starts_page_one_ok(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = FirstChapterStartsOnPageOneCheck().run(doc, word_assignment)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize(
    "filename",
    [
        "ok_continuos_section.docx",
    ],
)
def test_continuous_first_chapter_starts_page_one_ok(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = FirstChapterStartsOnPageOneCheck().run(doc, word_assignment)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize(
    "filename",
    [
        "fail.docx",
        "fail.odt",
    ],
)
def test_first_chapter_starts_page_one_fail(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = FirstChapterStartsOnPageOneCheck().run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None
