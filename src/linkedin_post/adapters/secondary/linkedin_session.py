"""SessionGate over upstream's signed-in Patchright browser."""

from fastmcp.server.dependencies import get_context
from linkedin_mcp_server.dependencies import get_or_create_browser, get_ready_extractor
from patchright.async_api import Page


class UpstreamSessionGate:
    async def open(self, tool_name: str) -> Page:
        # Upstream's gate: bootstrap checks, browser start, authentication.
        await get_ready_extractor(get_context(), tool_name=tool_name)
        browser = await get_or_create_browser()
        return browser.page
