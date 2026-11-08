# Copyright (c) 2026 Dmitry Andersson
# SPDX-License-Identifier: MIT
"""Outcomes of publishing and deleting a post.

``retry_safe`` is the rule a caller relies on: False means LinkedIn may already
have acted, so calling again could post twice.
"""

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any


class PublishStatus(StrEnum):
    """How a create_post call ended."""

    POSTED = "posted"
    DRY_RUN = "dry_run"
    OUTCOME_UNKNOWN = "outcome_unknown"
    INVALID_TEXT = "invalid_text"
    EDITOR_NOT_FOUND = "editor_not_found"
    INSERT_FAILED = "insert_failed"


class DeleteStatus(StrEnum):
    """How a delete_post call ended."""

    DELETED = "deleted"
    DRY_RUN = "dry_run"
    INVALID_POST = "invalid_post"
    POST_NOT_FOUND = "post_not_found"
    NOT_DELETABLE = "not_deletable"
    CONFIRM_NOT_FOUND = "confirm_not_found"
    OUTCOME_UNKNOWN = "outcome_unknown"


# Post was clicked: the post may exist even if we couldn't see it appear.
_PUBLISH_NOT_RETRY_SAFE = frozenset({PublishStatus.POSTED, PublishStatus.OUTCOME_UNKNOWN})


def _drop_none(fields: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in fields.items() if value is not None}


@dataclass(frozen=True, slots=True)
class PublishResult:
    """Result of create_post; ``posted`` and ``retry_safe`` follow from ``status``."""

    status: PublishStatus
    message: str
    visibility: str | None = None
    post_url: str | None = None
    characters: int | None = None
    url: str | None = None
    trace_dir: str | None = None

    @property
    def posted(self) -> bool:
        """Whether LinkedIn published the post."""
        return self.status is PublishStatus.POSTED

    @property
    def retry_safe(self) -> bool:
        """Whether calling again can't publish the post twice."""
        return self.status not in _PUBLISH_NOT_RETRY_SAFE

    def to_dict(self) -> dict[str, Any]:
        """Serialize for the MCP tool, leaving out unset fields."""
        return {
            **_drop_none(asdict(self)),
            "status": self.status.value,
            "posted": self.posted,
            "retry_safe": self.retry_safe,
        }


@dataclass(frozen=True, slots=True)
class DeleteResult:
    """Result of delete_post; ``deleted`` follows from ``status``."""

    status: DeleteStatus
    message: str
    url: str | None = None
    trace_dir: str | None = None

    @property
    def deleted(self) -> bool:
        """Whether LinkedIn deleted the post."""
        return self.status is DeleteStatus.DELETED

    @property
    def retry_safe(self) -> bool:
        """Always True: deleting twice is harmless, the post is gone or still there."""
        return True

    def to_dict(self) -> dict[str, Any]:
        """Serialize for the MCP tool, leaving out unset fields."""
        return {
            **_drop_none(asdict(self)),
            "status": self.status.value,
            "deleted": self.deleted,
            "retry_safe": self.retry_safe,
        }
