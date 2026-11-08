"""Failure diagnostics through upstream's page trace (screenshot, URL, title, body)."""

import logging
from typing import Any

from linkedin_mcp_server.debug_trace import mark_trace_for_retention, record_page_trace
from patchright.async_api import Page

logger = logging.getLogger(__name__)


async def capture_failure(page: Page, step: str, extra: dict[str, Any] | None = None) -> str | None:
    """Record the page and keep the trace run. Returns its directory; never raises.

    Writes nothing when LINKEDIN_TRACE_MODE=off.
    """
    try:
        await record_page_trace(page, step, extra={"frames": [f.url for f in page.frames], **(extra or {})})
        trace_dir = mark_trace_for_retention()
    except Exception:
        logger.exception("failure trace for %s could not be recorded", step)
        return None
    return str(trace_dir) if trace_dir is not None else None
