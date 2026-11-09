# Copyright (c) 2026 Dmitry Andersson
# SPDX-License-Identifier: MIT
"""What the domain needs from LinkedIn.

The page handle is opaque to the domain: the session gate hands one out and
the composer and remover act on it.
"""

from typing import Protocol

from linkedin_post.domain.entities import (
    DeleteResult,
    PostMedia,
    PostRef,
    PostText,
    PublishResult,
)

type PageHandle = object


class SessionGate(Protocol):
    """Access to a signed-in LinkedIn page."""

    async def open(self, tool_name: str) -> PageHandle:
        """Return a signed-in page, or raise if the session can't be used."""
        ...


class PostComposer(Protocol):
    """LinkedIn's share dialog."""

    async def publish(
        self, page: PageHandle, text: PostText, media: PostMedia, *, confirm: bool
    ) -> PublishResult:
        """Insert ``text``, attach ``media`` and click Post, or discard when not ``confirm``."""
        ...


class PostRemover(Protocol):
    """LinkedIn's post menu and delete confirmation."""

    async def delete(self, page: PageHandle, post: PostRef, *, confirm: bool) -> DeleteResult:
        """Delete ``post``, or only check its menu offers Delete when not ``confirm``."""
        ...
