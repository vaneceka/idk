from pathlib import Path

import pytest

from checks.word.objects.object_caption_check import ObjectCaptionCheck
from tests.utils.load_document import load_document

BASE = Path(__file__).parent


@pytest.mark.parametrize(
    "filename",
    ["ok.docx", "ok.odt", "ok_table.docx"],
)
def test_objects_caption_ok(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = ObjectCaptionCheck().run(doc, word_assignment)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize(
    "filename",
    ["fail.docx", "fail.odt", "fail_table.docx"],
)
def test_objects_caption_fail(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = ObjectCaptionCheck().run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None
