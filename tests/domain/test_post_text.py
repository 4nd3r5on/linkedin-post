import pytest

from linkedin_post.domain.entities import InvalidPostText, PostText


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
        ("emoji 🐧 and #tags", "emoji 🐧 and #tags"),
    ],
)
def test_normalizes_line_breaks_and_trims(raw: str, expected: str) -> None:
    assert PostText.parse(raw).value == expected


@pytest.mark.parametrize("raw", ["", "   ", "\n\r\n  ", " "])
def test_refuses_blank_text(raw: str) -> None:
    with pytest.raises(InvalidPostText, match="non-whitespace"):
        PostText.parse(raw)


@pytest.mark.parametrize("raw", ["bell\x07", "nul\x00", "del\x7f", "esc\x1b[0m", "ls x", "ps x"])
def test_refuses_control_characters(raw: str) -> None:
    with pytest.raises(InvalidPostText, match="control characters"):
        PostText.parse(raw)


def test_tab_is_refused_like_other_controls() -> None:
    with pytest.raises(InvalidPostText, match="control characters"):
        PostText.parse("a\tb")


def test_length_counts_normalized_text() -> None:
    assert len(PostText.parse("  ab\r\ncd  ")) == len("ab\ncd")
