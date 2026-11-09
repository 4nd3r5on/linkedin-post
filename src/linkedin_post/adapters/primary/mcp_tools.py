# Copyright (c) 2026 Dmitry Andersson
# SPDX-License-Identifier: MIT
"""create_post and delete_post as MCP tools, shaped like upstream's send_message."""

import logging
from typing import Any

from fastmcp import Context, FastMCP
from linkedin_mcp_server.config.schema import DEFAULT_TOOL_TIMEOUT_SECONDS
from linkedin_mcp_server.dependencies import tool_errors

from linkedin_post.domain.ports.primary.posting import Posting

logger = logging.getLogger(__name__)


def register_posting_tools(
    mcp: FastMCP, posting: Posting, *, tool_timeout: float = DEFAULT_TOOL_TIMEOUT_SECONDS
) -> None:
    """Register create_post and delete_post on ``mcp``, backed by ``posting``."""

    @mcp.tool(
        timeout=tool_timeout,
        title="Create Post",
        annotations={"readOnlyHint": False, "openWorldHint": True},
        tags={"post"},
    )
    @tool_errors
    async def create_post(
        text: str,
        *,
        confirm_post: bool,
        ctx: Context,
        images: list[str] | None = None,
    ) -> dict[str, Any]:
        """Publish a post, optionally with images, to the signed-in user's LinkedIn feed.

        Opens LinkedIn's share dialog, inserts the text, attaches the images
        and clicks Post. The
        post uses the dialog's current visibility ("Post to Anyone" by
        default), which is returned as ``visibility``. With confirm_post False
        this is a dry run: the text is inserted, then the draft is discarded
        and nothing is published.

        Args:
            text: Post text. LF/CRLF/CR end a line; empty lines are kept.
                Control characters other than line breaks are refused. May be
                empty when images are given.
            confirm_post: Must be True to publish. False is a dry run.
            ctx: FastMCP context for progress reporting
            images: Absolute paths, on the machine running this server, of up
                to 20 JPEG/PNG/GIF images of at most 5 MB each.

        Returns:
            Dict with status ("dry_run", "posted", "outcome_unknown",
            "invalid_text", "invalid_media", "media_rejected",
            "editor_not_found", "insert_failed"), posted,
            visibility, post_url (when LinkedIn shows one), trace_dir (on
            failures, when tracing is on) and retry_safe.
            retry_safe is False once Post was clicked: calling again while it
            is False can publish the post twice. Check the feed instead.

        """
        await ctx.report_progress(progress=0, total=100, message="Opening share dialog")
        result = await posting.create_post(text, images=images, confirm=confirm_post)
        await ctx.report_progress(progress=100, total=100, message="Complete")
        logger.info("create_post: status=%s", result.status)
        return result.to_dict()

    @mcp.tool(
        timeout=tool_timeout,
        title="Delete Post",
        annotations={"readOnlyHint": False, "destructiveHint": True, "openWorldHint": True},
        tags={"post"},
    )
    @tool_errors
    async def delete_post(post: str, *, confirm_delete: bool, ctx: Context) -> dict[str, Any]:
        """Delete one of the signed-in user's LinkedIn posts. Cannot be undone.

        Opens the post, uses its "..." menu and LinkedIn's own confirmation.
        Only works on the user's own posts; anyone else's has no Delete item
        and returns not_deletable. With confirm_delete False this is a dry
        run that checks the post exists and is deletable.

        Args:
            post: Post URL (the post_url from create_post, a /feed/update/
                link, or a /posts/...-activity-<id>-... permalink) or URN
                (urn:li:activity:<id>, urn:li:share:<id>, urn:li:ugcPost:<id>).
            confirm_delete: Must be True to delete. False is a dry run.
            ctx: FastMCP context for progress reporting

        Returns:
            Dict with status ("deleted", "dry_run", "invalid_post",
            "post_not_found", "not_deletable", "confirm_not_found",
            "outcome_unknown"), deleted, url and message.

        """
        await ctx.report_progress(progress=0, total=100, message="Opening post")
        result = await posting.delete_post(post, confirm=confirm_delete)
        await ctx.report_progress(progress=100, total=100, message="Complete")
        logger.info("delete_post: status=%s", result.status)
        return result.to_dict()
