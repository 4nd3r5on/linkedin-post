import pytest

from linkedin_post.domain.entities import DeleteStatus, PublishStatus
from linkedin_post.domain.services.posting import PostingService
from tests.fakes import PAGE, FakeComposer, FakeRemover, FakeSession

pytestmark = pytest.mark.anyio

ID = "7525284009694609408"


@pytest.fixture
def ports() -> tuple[FakeSession, FakeComposer, FakeRemover]:
    return FakeSession(), FakeComposer(), FakeRemover()


@pytest.fixture
def service(ports: tuple[FakeSession, FakeComposer, FakeRemover]) -> PostingService:
    return PostingService(*ports)


async def test_invalid_text_never_opens_the_browser(service, ports) -> None:
    session, composer, _ = ports
    result = await service.create_post("bad\x07", confirm=True)
    assert result.status is PublishStatus.INVALID_TEXT
    assert result.retry_safe
    assert session.opened == [] and composer.calls == []


@pytest.mark.parametrize("confirm", [True, False])
async def test_create_passes_normalized_text_and_confirm(service, ports, confirm: bool) -> None:
    session, composer, _ = ports
    result = await service.create_post(" hi\r\nthere ", confirm=confirm)
    assert session.opened == ["create_post"]
    [(page, text, passed_confirm)] = composer.calls
    assert page is PAGE and text.value == "hi\nthere" and passed_confirm is confirm
    assert result.status is (PublishStatus.POSTED if confirm else PublishStatus.DRY_RUN)


async def test_invalid_post_ref_never_opens_the_browser(service, ports) -> None:
    session, _, remover = ports
    result = await service.delete_post("not a post", confirm=True)
    assert result.status is DeleteStatus.INVALID_POST
    assert session.opened == [] and remover.calls == []


@pytest.mark.parametrize("confirm", [True, False])
async def test_delete_resolves_ref_and_passes_confirm(service, ports, confirm: bool) -> None:
    session, _, remover = ports
    result = await service.delete_post(f"urn:li:activity:{ID}", confirm=confirm)
    assert session.opened == ["delete_post"]
    [(page, ref, passed_confirm)] = remover.calls
    assert page is PAGE and passed_confirm is confirm
    assert ref.url == f"https://www.linkedin.com/feed/update/urn:li:activity:{ID}/"
    assert result.deleted is confirm
