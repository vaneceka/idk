from pathlib import Path

import pytest

from checks.word.formatting.unnumbered_special_headings_check import (
    UnnumberedSpecialHeadingsCheck,
)
from tests.utils.load_document import load_document

BASE = Path(__file__).parent


@pytest.mark.parametrize(
    "filename",
    ["ok.docx", "ok.odt"],
)
def test_unnumbered_special_headings_ok(filename, word_assignment):
    doc = load_document(BASE / filename)
    check = UnnumberedSpecialHeadingsCheck()

    result = check.run(doc, word_assignment)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize(
    "filename",
    ["fail.docx", "fail.odt"],
)
def test_unnumbered_special_headings_fail(filename, word_assignment):
    doc = load_document(BASE / filename)
    check = UnnumberedSpecialHeadingsCheck()

    result = check.run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None
