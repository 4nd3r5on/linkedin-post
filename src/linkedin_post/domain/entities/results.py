"""Outcomes of publishing and deleting a post.

``retry_safe`` is the rule a caller relies on: False means LinkedIn may already
have acted, so calling again could post twice.
"""

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any


class PublishStatus(StrEnum):
    POSTED = "posted"
    DRY_RUN = "dry_run"
    OUTCOME_UNKNOWN = "outcome_unknown"
    INVALID_TEXT = "invalid_text"
    EDITOR_NOT_FOUND = "editor_not_found"
    INSERT_FAILED = "insert_failed"


class DeleteStatus(StrEnum):
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
    status: PublishStatus
    message: str
    visibility: str | None = None
    post_url: str | None = None
    characters: int | None = None
    url: str | None = None
    trace_dir: str | None = None

    @property
    def posted(self) -> bool:
        return self.status is PublishStatus.POSTED

    @property
    def retry_safe(self) -> bool:
        return self.status not in _PUBLISH_NOT_RETRY_SAFE

    def to_dict(self) -> dict[str, Any]:
        fields = _drop_none(asdict(self))
        return {
            **fields,
            "status": self.status.value,
            "posted": self.posted,
            "retry_safe": self.retry_safe,
        }


@dataclass(frozen=True, slots=True)
class DeleteResult:
    status: DeleteStatus
    message: str
    url: str | None = None

    @property
    def deleted(self) -> bool:
        return self.status is DeleteStatus.DELETED

    @property
    def retry_safe(self) -> bool:
        # Deleting twice is harmless: the post is either gone or still there.
        return True

    def to_dict(self) -> dict[str, Any]:
        fields = _drop_none(asdict(self))
        return {
            **fields,
            "status": self.status.value,
            "deleted": self.deleted,
            "retry_safe": self.retry_safe,
        }
