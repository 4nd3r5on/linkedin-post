import pytest
from fastmcp import Client, FastMCP

from linkedin_post.adapters.primary.mcp_tools import register_posting_tools
from linkedin_post.domain.services.posting import PostingService
from tests.fakes import FakeComposer, FakeRemover, FakeSession

pytestmark = pytest.mark.anyio


@pytest.fixture
def mcp() -> FastMCP:
    server = FastMCP("test")
    register_posting_tools(server, PostingService(FakeSession(), FakeComposer(), FakeRemover()))
    return server


async def test_tools_are_registered_with_arguments(mcp: FastMCP) -> None:
    async with Client(mcp) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}
    assert set(tools) == {"create_post", "delete_post"}
    assert set(tools["create_post"].input_schema["required"]) == {"text", "confirm_post"}
    assert set(tools["delete_post"].input_schema["required"]) == {"post", "confirm_delete"}
    assert tools["delete_post"].annotations.destructive_hint is True


async def test_create_post_returns_result_dict(mcp: FastMCP) -> None:
    async with Client(mcp) as client:
        result = await client.call_tool("create_post", {"text": "hi", "confirm_post": False})
    assert result.structured_content["status"] == "dry_run"
    assert result.structured_content["retry_safe"] is True


async def test_delete_post_rejects_bad_ref(mcp: FastMCP) -> None:
    async with Client(mcp) as client:
        result = await client.call_tool("delete_post", {"post": "nope", "confirm_delete": True})
    assert result.structured_content["status"] == "invalid_post"
