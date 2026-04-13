from pathlib import Path

import pytest

from checks.word.structure.document_structure_check import DocumentStructureCheck
from tests.utils.load_document import load_document

BASE = Path(__file__).parent


@pytest.mark.parametrize(
    "filename",
    [
        "ok.docx",
        "ok.odt",
    ],
)
def test_document_structure_ok(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = DocumentStructureCheck().run(doc, word_assignment)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize(
    "filename",
    [
        "fail_no_continuous_levels.docx",
        "fail_no_continuous_levels.odt",
        "fail_no_h1_first.docx",
        "fail_no_h1_first.odt",
    ],
)
def test_document_structure_fail(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = DocumentStructureCheck().run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None
