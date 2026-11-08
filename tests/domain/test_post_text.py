# Copyright (c) 2026 Dmitry Andersson
# SPDX-License-Identifier: MIT
import pytest

from linkedin_post.domain.entities import (
    BlankPostError,
    ControlCharacterError,
    InvalidPostTextError,
    PostText,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("hello", "hello"),
        ("  hello  ", "hello"),
        ("a\r\nb\rc\nd", "a\nb\nc\nd"),
        ("first\n\n\nsecond", "first\n\n\nsecond"),
        ("first\n   \nsecond", "first\n\nsecond"),
        ("\n\n  body  \n\n", "body"),
        ("  indented line\nnext", "indented line\nnext"),
        ("emoji \U0001f427 and #tags", "emoji \U0001f427 and #tags"),
    ],
)
def test_normalizes_line_breaks_and_trims(raw: str, expected: str) -> None:
    assert PostText.parse(raw).value == expected


@pytest.mark.parametrize("raw", ["", "   ", "\n\r\n  ", "\xa0"])
def test_refuses_blank_text(raw: str) -> None:
    with pytest.raises(BlankPostError, match="non-whitespace"):
        PostText.parse(raw)


@pytest.mark.parametrize(
    "raw",
    ["bell\x07", "nul\x00", "del\x7f", "esc\x1b[0m", "tab\tx", "ls\u2028x", "ps\u2029x"],
)
def test_refuses_control_characters(raw: str) -> None:
    with pytest.raises(ControlCharacterError, match="control characters"):
        PostText.parse(raw)


def test_both_refusals_are_invalid_post_text() -> None:
    assert issubclass(BlankPostError, InvalidPostTextError)
    assert issubclass(ControlCharacterError, InvalidPostTextError)


def test_length_counts_normalized_text() -> None:
    assert len(PostText.parse("  ab\r\ncd  ")) == len("ab\ncd")
