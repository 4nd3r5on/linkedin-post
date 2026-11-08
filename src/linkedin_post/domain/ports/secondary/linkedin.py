"""What the domain needs from LinkedIn.

The page handle is opaque to the domain: the session gate hands one out and
the composer and remover act on it.
"""

from typing import Protocol

from linkedin_post.domain.entities import DeleteResult, PostRef, PostText, PublishResult

type PageHandle = object


class SessionGate(Protocol):
    async def open(self, tool_name: str) -> PageHandle:
        """Return a signed-in page, or raise if the session can't be used."""
        ...


class PostComposer(Protocol):
    async def publish(self, page: PageHandle, text: PostText, *, confirm: bool) -> PublishResult: ...


class PostRemover(Protocol):
    async def delete(self, page: PageHandle, post: PostRef, *, confirm: bool) -> DeleteResult: ...
