from pathlib import Path

import pytest

from checks.word.formatting.custom_style_with_tabs_check import CustomStyleWithTabsCheck
from tests.utils.load_document import load_document

BASE = Path(__file__).parent


@pytest.mark.parametrize(
    "filename",
    [
        "ok.docx",
        "ok.odt",
    ],
)
def test_custom_tabs_style_ok(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = CustomStyleWithTabsCheck().run(doc, word_assignment)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize(
    "filename",
    [
        "fail_dont_exist.docx",
        "fail_dont_exist.odt",
    ],
)
def test_custom_tabs_style_dont_exist_fail(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = CustomStyleWithTabsCheck().run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None


@pytest.mark.parametrize(
    "filename",
    [
        "fail_invalid_tabs.docx",
        "fail_invalid_tabs.odt",
    ],
)
def test_custom_tabs_style_invalid_tabs_fail(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = CustomStyleWithTabsCheck().run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None
