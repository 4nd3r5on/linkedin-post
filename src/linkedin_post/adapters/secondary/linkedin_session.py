# Copyright (c) 2026 Dmitry Andersson
# SPDX-License-Identifier: MIT
"""SessionGate over upstream's signed-in Patchright browser."""

from typing import override

from fastmcp.server.dependencies import get_context
from linkedin_mcp_server.dependencies import get_or_create_browser, get_ready_extractor
from patchright.async_api import Page

from linkedin_post.domain.ports.secondary.linkedin import SessionGate


class UpstreamSessionGate(SessionGate):
    """Upstream's auth gate and shared browser, for the current MCP request."""

    @override
    async def open(self, tool_name: str) -> Page:
        # Upstream's gate: bootstrap checks, browser start, authentication.
        await get_ready_extractor(get_context(), tool_name=tool_name)
        browser = await get_or_create_browser()
        return browser.page
