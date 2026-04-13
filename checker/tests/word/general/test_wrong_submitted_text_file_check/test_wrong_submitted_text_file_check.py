from pathlib import Path

import pytest

from checks.word.general.wrong_submitted_text_file_check import (
    WrongSubmittedTextFileCheck,
)

BASE = Path(__file__).parent


@pytest.mark.parametrize(
    "filename",
    [
        "ok.docx",
        "ok.odt",
    ],
)
def test_wrong_submitted_text_file_check_ok(filename):
    path = BASE / filename
    result = WrongSubmittedTextFileCheck().run_on_path(path)

    assert result.passed is True
    assert result.points == 0


@pytest.mark.parametrize(
    "filename",
    [
        "fail.dt",
        "fail.doc",
    ],
)
def test_wrong_submitted_text_file_check_fail(filename):
    path = BASE / filename
    result = WrongSubmittedTextFileCheck().run_on_path(path)

    assert result.passed is False
    assert result.points is None
