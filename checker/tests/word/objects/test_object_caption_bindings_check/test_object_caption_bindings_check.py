from pathlib import Path

import pytest

from checks.word.objects.object_caption_bindings_check import ObjectCaptionBindingCheck
from tests.utils.load_document import load_document

BASE = Path(__file__).parent


@pytest.mark.parametrize(
    "filename",
    [
        "ok.docx",
        "ok_manual_caption_bind.docx",
        "ok.odt",

    ],
)
def test_objects_binding_ok(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = ObjectCaptionBindingCheck().run(doc, word_assignment)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize(
    "filename",
    [
        "fail.docx",
        "fail.odt",
    ],
)
def test_objects_binding_fail(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = ObjectCaptionBindingCheck().run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None


@pytest.mark.parametrize(
    "filename",
    [
        "fail_group.docx",
    ],
)
def test_objects_not_in_group_fail(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = ObjectCaptionBindingCheck().run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None

@pytest.mark.parametrize(
    "filename",
    [
        "ok_table.docx",
    ],
)
def test_objects_caption_binding_table_ok(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = ObjectCaptionBindingCheck().run(doc, word_assignment)

    assert result.passed is True
    assert result.points == 0

@pytest.mark.parametrize(
    "filename",
    [
        "fail_chart.docx",
    ],
)
def test_objects_caption_binding_chart_fail(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = ObjectCaptionBindingCheck().run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None

@pytest.mark.parametrize(
    "filename",
    [
        "ok_chart.docx",
        "ok_chart.odt"
    ],
)
def test_objects_caption_binding_chart_ok(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = ObjectCaptionBindingCheck().run(doc, word_assignment)

    assert result.passed is True
    assert result.points == 0