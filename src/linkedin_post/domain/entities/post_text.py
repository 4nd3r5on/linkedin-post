"""The text of a post, checked and normalized before any browser work starts."""

from dataclasses import dataclass

# Upstream's own rules for text typed into LinkedIn's editor, so a post is
# accepted or refused exactly like a message from send_message.
from linkedin_mcp_server.linkedin.contracts import (
    _refused_character,
    normalize_message_text,
)


class InvalidPostText(ValueError):
    """The text can't be posted; nothing was sent to LinkedIn."""


@dataclass(frozen=True, slots=True)
class PostText:
    value: str

    @classmethod
    def parse(cls, raw: str) -> "PostText":
        """Refuse control characters and blank text; normalize line breaks.

        LF, CRLF and CR all end a line, whitespace-only lines become empty and
        the whole text is trimmed, matching what LinkedIn itself publishes.
        """
        if any(_refused_character(c) for c in raw):
            raise InvalidPostText("Post must not contain control characters other than line breaks.")
        normalized = normalize_message_text(raw)
        if not normalized:
            raise InvalidPostText("Post must contain non-whitespace characters.")
        return cls(normalized)

    def __len__(self) -> int:
        return len(self.value)
