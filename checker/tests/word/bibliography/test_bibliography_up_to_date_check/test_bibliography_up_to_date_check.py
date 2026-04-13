from pathlib import Path

import pytest

from checks.word.bibliography.bibliography_up_to_date_check import (
    BibliographyNotUpdatedCheck,
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
def test_bibliography_up_to_date_check_ok(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = BibliographyNotUpdatedCheck().run(doc, word_assignment)

    assert result.passed is True
    assert result.points == 0

@pytest.mark.parametrize(
    "filename",
    [
        "ok_order.docx",
        "ok_order.odt",
    ],
)
def test_bibliography_up_to_date_order_ok(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = BibliographyNotUpdatedCheck().run(doc, word_assignment)

    assert result.passed is True
    assert result.points == 0

@pytest.mark.parametrize(
   "filename",
    [
        "fail_order.docx",
        "fail_order.odt",
    ],
)
def test_bibliography_up_to_date_order_fail(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = BibliographyNotUpdatedCheck().run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None


@pytest.mark.parametrize(
    "filename",
    ["fail.docx", "fail.odt", "fail_extra_cit.docx", "fail_extra_cit.odt"],
)
def test_bibliography_up_to_date_check_fail(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = BibliographyNotUpdatedCheck().run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None
