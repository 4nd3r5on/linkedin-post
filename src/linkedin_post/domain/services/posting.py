# Copyright (c) 2026 Dmitry Andersson
# SPDX-License-Identifier: MIT
"""Create and delete posts: validate first, touch the browser only for valid input."""

from typing import override

from linkedin_post.domain.entities import (
    DeleteResult,
    DeleteStatus,
    InvalidPostRefError,
    InvalidPostTextError,
    PostRef,
    PostText,
    PublishResult,
    PublishStatus,
)
from linkedin_post.domain.ports.primary.posting import Posting
from linkedin_post.domain.ports.secondary.linkedin import (
    PostComposer,
    PostRemover,
    SessionGate,
)


class PostingService(Posting):
    """The ``Posting`` port, on top of the LinkedIn secondary ports."""

    def __init__(self, session: SessionGate, composer: PostComposer, remover: PostRemover) -> None:
        """Use ``session`` for a signed-in page and act on it with the others."""
        self._session = session
        self._composer = composer
        self._remover = remover

    @override
    async def create_post(self, text: str, *, confirm: bool) -> PublishResult:
        try:
            post_text = PostText.parse(text)
        except InvalidPostTextError as refusal:
            return PublishResult(PublishStatus.INVALID_TEXT, str(refusal))
        page = await self._session.open("create_post")
        return await self._composer.publish(page, post_text, confirm=confirm)

    @override
    async def delete_post(self, post: str, *, confirm: bool) -> DeleteResult:
        try:
            ref = PostRef.parse(post)
        except InvalidPostRefError as refusal:
            return DeleteResult(DeleteStatus.INVALID_POST, str(refusal))
        page = await self._session.open("delete_post")
        return await self._remover.delete(page, ref, confirm=confirm)
