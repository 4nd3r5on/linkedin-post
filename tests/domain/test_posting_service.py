# Copyright (c) 2026 Dmitry Andersson
# SPDX-License-Identifier: MIT
"""PostingService with fake ports: validation order and what reaches the browser."""

from dataclasses import dataclass

import pytest

from linkedin_post.domain.entities import DeleteStatus, PublishStatus
from linkedin_post.domain.services.posting import PostingService
from tests.fakes import PAGE, FakeComposer, FakeRemover, FakeSession

pytestmark = pytest.mark.anyio

ID = "7525284009694609408"


@dataclass
class Ports:
    session: FakeSession
    composer: FakeComposer
    remover: FakeRemover


@pytest.fixture
def ports() -> Ports:
    return Ports(FakeSession(), FakeComposer(), FakeRemover())


@pytest.fixture
def service(ports: Ports) -> PostingService:
    return PostingService(ports.session, ports.composer, ports.remover)


async def test_invalid_text_never_opens_the_browser(service: PostingService, ports: Ports) -> None:
    result = await service.create_post("bad\x07", confirm=True)
    assert result.status is PublishStatus.INVALID_TEXT
    assert result.retry_safe
    assert ports.session.opened == []
    assert ports.composer.calls == []


@pytest.mark.parametrize("confirm", [True, False])
async def test_create_passes_normalized_text_and_confirm(
    service: PostingService, ports: Ports, confirm: bool
) -> None:
    result = await service.create_post(" hi\r\nthere ", confirm=confirm)
    assert ports.session.opened == ["create_post"]
    [(page, text, passed_confirm)] = ports.composer.calls
    assert page is PAGE
    assert text.value == "hi\nthere"
    assert passed_confirm is confirm
    assert result.status is (PublishStatus.POSTED if confirm else PublishStatus.DRY_RUN)


async def test_invalid_post_ref_never_opens_the_browser(
    service: PostingService, ports: Ports
) -> None:
    result = await service.delete_post("not a post", confirm=True)
    assert result.status is DeleteStatus.INVALID_POST
    assert ports.session.opened == []
    assert ports.remover.calls == []


@pytest.mark.parametrize("confirm", [True, False])
async def test_delete_resolves_ref_and_passes_confirm(
    service: PostingService, ports: Ports, confirm: bool
) -> None:
    result = await service.delete_post(f"urn:li:activity:{ID}", confirm=confirm)
    assert ports.session.opened == ["delete_post"]
    [(page, ref, passed_confirm)] = ports.remover.calls
    assert page is PAGE
    assert passed_confirm is confirm
    assert ref.url == f"https://www.linkedin.com/feed/update/urn:li:activity:{ID}/"
    assert result.deleted is confirm
