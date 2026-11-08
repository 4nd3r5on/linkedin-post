# Copyright (c) 2026 Dmitry Andersson
# SPDX-License-Identifier: MIT
"""What the outside world can ask of this app."""

from typing import Protocol

from linkedin_post.domain.entities import DeleteResult, PublishResult


class Posting(Protocol):
    """Create and delete the signed-in user's posts."""

    async def create_post(self, text: str, *, confirm: bool) -> PublishResult:
        """Publish ``text``; with ``confirm`` False, insert it and discard the draft."""
        ...

    async def delete_post(self, post: str, *, confirm: bool) -> DeleteResult:
        """Delete the post ``post`` names; with ``confirm`` False, only check it can be."""
        ...
