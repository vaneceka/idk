from pathlib import Path

import pytest

from checks.word.bibliography.unused_bibliography_source_check import (
    UnusedBibliographySourceCheck,
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
def test_header_footer_missing_style_ok(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = UnusedBibliographySourceCheck().run(doc, word_assignment)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize(
    "filename",
    [
        "fail.docx",
        "fail.odt",
    ],
)
def test_header_footer_missing_style_fail(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = UnusedBibliographySourceCheck().run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None
