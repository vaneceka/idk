from pathlib import Path

import pytest

from checks.word.structure.toc_illegal_content_check import TOCIllegalContentCheck
from tests.utils.load_document import load_document

BASE = Path(__file__).parent


@pytest.mark.parametrize(
    "filename",
    [
        "ok.docx",
        "ok.odt",
        "ok_fig_near_heading.docx"
    ],
)
def test_TOC_illegal_content_ok(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = TOCIllegalContentCheck().run(doc, word_assignment)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize(
    "filename",
    [
        "fail.docx",
        "fail.odt",
    ],
)
def test_TOC_illegal_content_fail(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = TOCIllegalContentCheck().run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None
