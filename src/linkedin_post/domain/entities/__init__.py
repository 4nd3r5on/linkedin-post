# Copyright (c) 2026 Dmitry Andersson
# SPDX-License-Identifier: MIT
"""Value objects and results of the posting domain."""

from linkedin_post.domain.entities.post_ref import InvalidPostRefError, PostRef
from linkedin_post.domain.entities.post_text import (
    BlankPostError,
    ControlCharacterError,
    InvalidPostTextError,
    PostText,
)
from linkedin_post.domain.entities.results import (
    DeleteResult,
    DeleteStatus,
    PublishResult,
    PublishStatus,
)

__all__ = [
    "BlankPostError",
    "ControlCharacterError",
    "DeleteResult",
    "DeleteStatus",
    "InvalidPostRefError",
    "InvalidPostTextError",
    "PostRef",
    "PostText",
    "PublishResult",
    "PublishStatus",
]
