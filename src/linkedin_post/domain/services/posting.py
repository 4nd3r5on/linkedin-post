"""Create and delete posts: validate first, touch the browser only for valid input."""

from linkedin_post.domain.entities import (
    DeleteResult,
    DeleteStatus,
    InvalidPostRef,
    InvalidPostText,
    PostRef,
    PostText,
    PublishResult,
    PublishStatus,
)
from linkedin_post.domain.ports.secondary.linkedin import (
    PostComposer,
    PostRemover,
    SessionGate,
)


class PostingService:
    """Implements the ``Posting`` primary port."""

    def __init__(self, session: SessionGate, composer: PostComposer, remover: PostRemover) -> None:
        self._session = session
        self._composer = composer
        self._remover = remover

    async def create_post(self, text: str, *, confirm: bool) -> PublishResult:
        try:
            post_text = PostText.parse(text)
        except InvalidPostText as refusal:
            return PublishResult(PublishStatus.INVALID_TEXT, str(refusal))
        page = await self._session.open("create_post")
        return await self._composer.publish(page, post_text, confirm=confirm)

    async def delete_post(self, post: str, *, confirm: bool) -> DeleteResult:
        try:
            ref = PostRef.parse(post)
        except InvalidPostRef as refusal:
            return DeleteResult(DeleteStatus.INVALID_POST, str(refusal))
        page = await self._session.open("delete_post")
        return await self._remover.delete(page, ref, confirm=confirm)
