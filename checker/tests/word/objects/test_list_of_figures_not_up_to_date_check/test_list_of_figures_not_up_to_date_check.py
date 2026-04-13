from pathlib import Path

import pytest

from checks.word.objects.list_of_figures_not_up_to_date_check import (
    ListOfFiguresNotUpdatedCheck,
)
from tests.utils.load_document import load_document

BASE = Path(__file__).parent


@pytest.mark.parametrize(
    "filename",
    [
        "ok.docx",
        "ok_citation_in_caption.docx",
        "ok.odt",
    ],
)
def test_list_of_figures_is_up_to_date_ok(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = ListOfFiguresNotUpdatedCheck().run(doc, word_assignment)

    assert result.passed is True
    assert result.points == 0
    assert "Seznam obrázků v dokumentu chybí" not in result.message


@pytest.mark.parametrize(
    "filename",
    [
        "fail_different_caption.docx",
        "fail_different_caption.odt",
        "fail_non_existing.docx",
        "fail_non_existing.odt",
        "fail_citation_in_caption.docx",
    ],
)
def test_list_of_figures_is_up_to_date_fail(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = ListOfFiguresNotUpdatedCheck().run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None
