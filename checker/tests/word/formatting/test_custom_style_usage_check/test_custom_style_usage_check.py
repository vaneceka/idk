from pathlib import Path

import pytest

from checks.word.formatting.custom_style_usage_check import (
    RequiredCustomStylesUsageCheck,
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
def test_custom_style_usage_ok(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = RequiredCustomStylesUsageCheck().run(doc, word_assignment)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize(
    "filename",
    [
        "fail.docx",
        "fail.odt",
    ],
)
def test_custom_style_usage_fail(filename, word_assignment):
    doc = load_document(BASE / filename)
    result = RequiredCustomStylesUsageCheck().run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None
