# Copyright (c) 2026 Dmitry Andersson
# SPDX-License-Identifier: MIT
"""The text of a post, checked and normalized before any browser work starts."""

from dataclasses import dataclass
from typing import Self

# Upstream's own rules for text typed into LinkedIn's editor, so a post is
# accepted or refused exactly like a message from send_message.
from linkedin_mcp_server.linkedin.contracts import (
    _refused_character,
    normalize_message_text,
)


class InvalidPostTextError(ValueError):
    """The text can't be posted; nothing was sent to LinkedIn."""


class ControlCharacterError(InvalidPostTextError):
    """The text has a control character other than a line break."""

    def __init__(self) -> None:
        """Explain which characters are refused."""
        super().__init__("Post must not contain control characters other than line breaks.")


class BlankPostError(InvalidPostTextError):
    """The text is empty or only whitespace."""

    def __init__(self) -> None:
        """Explain that some visible text is needed."""
        super().__init__("Post must contain non-whitespace characters.")


@dataclass(frozen=True, slots=True)
class PostText:
    """Post text as LinkedIn will publish it."""

    value: str

    @classmethod
    def parse(cls, raw: str, *, allow_blank: bool = False) -> Self:
        """Refuse control characters and blank text; normalize line breaks.

        LF, CRLF and CR all end a line, whitespace-only lines become empty and
        the whole text is trimmed, matching what LinkedIn itself publishes.
        ``allow_blank`` is for posts with images, where text is optional.

        Raises:
            ControlCharacterError: The text has a refused control character.
            BlankPostError: Nothing is left after normalizing.

        """
        if any(_refused_character(c) for c in raw):
            raise ControlCharacterError
        normalized = normalize_message_text(raw)
        if not normalized and not allow_blank:
            raise BlankPostError
        return cls(normalized)

    def __len__(self) -> int:
        """Count the characters of the normalized text."""
        return len(self.value)
