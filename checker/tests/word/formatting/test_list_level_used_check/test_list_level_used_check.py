from pathlib import Path

import pytest

from checks.word.formatting.list_level_used_check import ListLevelUsedCheck
from tests.utils.load_document import load_document

BASE = Path(__file__).parent


@pytest.mark.parametrize("filename", ["ok.docx", "ok.odt"])
@pytest.mark.parametrize("level", [1, 2])
def test_list_level_used_ok(filename, level, word_assignment):
    doc = load_document(BASE / filename)
    check = ListLevelUsedCheck(level)

    result = check.run(doc, word_assignment)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize("filename", ["fail.docx", "fail.odt"])
@pytest.mark.parametrize("level", [1, 2])
def test_list_level_used_fail(filename, level, word_assignment):
    doc = load_document(BASE / filename)
    check = ListLevelUsedCheck(level)

    result = check.run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None

@pytest.mark.parametrize("filename", ["fail_with_toc.docx", "fail_with_toc.odt"])
@pytest.mark.parametrize("level", [1, 2])
def test_list_level_used_with_TOC_or_ListOfObjects_fail(filename, level, word_assignment):
    doc = load_document(BASE / filename)
    check = ListLevelUsedCheck(level)

    result = check.run(doc, word_assignment)

    assert result.passed is False
    assert result.points is None
