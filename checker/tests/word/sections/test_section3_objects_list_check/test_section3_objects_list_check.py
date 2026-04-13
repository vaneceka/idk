from pathlib import Path

import pytest

from checks.word.sections.section3_object_list_check import Section3ObjectsListsCheck
from tests.utils.load_document import load_document

BASE = Path(__file__).parent


@pytest.mark.parametrize(
    "filename",
    [
        "ok.docx",
        "ok.odt",
    ],
)
def test_section_3_object_list_ok(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = Section3ObjectsListsCheck().run(doc, word_assignment)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize(
    "filename",
    [
        "fail.docx",
        "fail.odt",
    ],
)
def test_section_3_object_list_fail(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = Section3ObjectsListsCheck().run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None
