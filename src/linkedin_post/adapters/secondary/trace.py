"""Failure diagnostics through upstream's page trace (screenshot, URL, title, body)."""

import logging
import re
from typing import Any

from linkedin_mcp_server.debug_trace import mark_trace_for_retention, record_page_trace
from patchright.async_api import Locator, Page

logger = logging.getLogger(__name__)

_HTML_LIMIT = 400
_PER_KIND_LIMIT = 10


async def _outer_html(locator: Locator) -> list[str]:
    html = []
    for element in (await locator.all())[:_PER_KIND_LIMIT]:
        try:
            html.append((await element.evaluate("el => el.outerHTML", timeout=1000))[:_HTML_LIMIT])
        except Exception as e:
            html.append(f"<error: {e}>")
    return html


async def _controls(page: Page, button_name: re.Pattern[str] | None) -> list[dict[str, Any]]:
    """Per frame: dialogs and the buttons named like the one we looked for.

    Role locators see native <dialog>, ARIA dialogs and open shadow roots, so
    this shows what our own locators could have matched.
    """
    frames = []
    for frame in page.frames:
        entry: dict[str, Any] = {"url": frame.url}
        try:
            entry["dialogs"] = await _outer_html(
                frame.get_by_role("dialog").or_(frame.get_by_role("alertdialog"))
            )
            if button_name is not None:
                entry["buttons"] = await _outer_html(frame.get_by_role("button", name=button_name))
        except Exception as e:
            entry["error"] = str(e)
        frames.append(entry)
    return frames


async def capture_failure(
    page: Page,
    step: str,
    extra: dict[str, Any] | None = None,
    *,
    button_name: re.Pattern[str] | None = None,
) -> str | None:
    """Record the page and keep the trace run. Returns its directory; never raises.

    Writes nothing when LINKEDIN_TRACE_MODE=off.
    """
    try:
        controls = await _controls(page, button_name)
        await record_page_trace(page, step, extra={"frames": controls, **(extra or {})})
        trace_dir = mark_trace_for_retention()
    except Exception:
        logger.exception("failure trace for %s could not be recorded", step)
        return None
    return str(trace_dir) if trace_dir is not None else None
