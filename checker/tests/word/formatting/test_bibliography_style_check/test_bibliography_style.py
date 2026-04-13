from pathlib import Path

import pytest

from checks.word.formatting.bibliography_style_check import BibliographyStyleCheck
from tests.utils.load_document import load_document

BASE = Path(__file__).parent


@pytest.mark.parametrize(
    "filename",
    [
        "ok.docx",
        "ok.odt",
    ],
)
def test_bibliography_style_ok(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = BibliographyStyleCheck().run(doc, word_assignment)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize(
    "filename",
    [
        "fail.docx",
        "fail.odt",
    ],
)
def test_bibliography_style_fail(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = BibliographyStyleCheck().run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None
