import pytest
from fastmcp import Client, FastMCP

from linkedin_post.composition.upstream import _original_register_post_tools, register_post_tools

pytestmark = pytest.mark.anyio


async def test_hook_adds_our_tools_next_to_upstreams() -> None:
    upstream_only, hooked = FastMCP("upstream"), FastMCP("hooked")
    _original_register_post_tools(upstream_only, tool_timeout=30)
    register_post_tools(hooked, tool_timeout=30)
    async with Client(upstream_only) as client:
        upstream_names = {tool.name for tool in await client.list_tools()}
    async with Client(hooked) as client:
        hooked_names = {tool.name for tool in await client.list_tools()}
    assert upstream_names, "upstream registered no post tools"
    assert hooked_names == upstream_names | {"create_post", "delete_post"}
