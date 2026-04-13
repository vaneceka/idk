from pathlib import Path

import pytest

from checks.word.formatting.heading_hierarchical_numbering_check import (
    HeadingHierarchicalNumberingCheck,
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
def test_heading_hierarchical_numbering_ok(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = HeadingHierarchicalNumberingCheck().run(doc, word_assignment)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize(
    "filename",
    [
        "fail.docx",
        "fail.odt",
    ],
)
def test_heading_hierarchical_numbering_file(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = HeadingHierarchicalNumberingCheck().run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None
