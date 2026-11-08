"""What the outside world can ask of this app."""

from typing import Protocol

from linkedin_post.domain.entities import DeleteResult, PublishResult


class Posting(Protocol):
    async def create_post(self, text: str, *, confirm: bool) -> PublishResult: ...

    async def delete_post(self, post: str, *, confirm: bool) -> DeleteResult: ...
