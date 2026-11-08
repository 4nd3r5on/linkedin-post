"""In-memory stand-ins for the secondary ports."""

from dataclasses import dataclass, field

from linkedin_post.domain.entities import (
    DeleteResult,
    DeleteStatus,
    PostRef,
    PostText,
    PublishResult,
    PublishStatus,
)

PAGE = object()


@dataclass
class FakeSession:
    opened: list[str] = field(default_factory=list)

    async def open(self, tool_name: str) -> object:
        self.opened.append(tool_name)
        return PAGE


@dataclass
class FakeComposer:
    calls: list[tuple[object, PostText, bool]] = field(default_factory=list)

    async def publish(self, page: object, text: PostText, *, confirm: bool) -> PublishResult:
        self.calls.append((page, text, confirm))
        status = PublishStatus.POSTED if confirm else PublishStatus.DRY_RUN
        return PublishResult(status, "fake", characters=len(text))


@dataclass
class FakeRemover:
    calls: list[tuple[object, PostRef, bool]] = field(default_factory=list)

    async def delete(self, page: object, post: PostRef, *, confirm: bool) -> DeleteResult:
        self.calls.append((page, post, confirm))
        status = DeleteStatus.DELETED if confirm else DeleteStatus.DRY_RUN
        return DeleteResult(status, "fake", post.url)
