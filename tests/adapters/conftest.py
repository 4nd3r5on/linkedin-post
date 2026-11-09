# Copyright (c) 2026 Dmitry Andersson
# SPDX-License-Identifier: MIT
"""A real headless Chromium for the browser-backed adapter tests."""

import os
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from patchright.async_api import Browser, async_playwright
from patchright.async_api import Error as PlaywrightError

# LINKEDIN_POST_TEST_CHROME, else upstream's managed Chromium, else patchright's
# own (`patchright install chromium`, as CI does).
_UPSTREAM_CHROME = "~/.linkedin-mcp/patchright-browsers/chromium-1248/chrome-linux64/chrome"
_CHROME = Path(os.environ.get("LINKEDIN_POST_TEST_CHROME", _UPSTREAM_CHROME)).expanduser()


@pytest.fixture
async def browser() -> AsyncIterator[Browser]:
    executable = str(_CHROME) if _CHROME.exists() else None
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True, executable_path=executable)
        except PlaywrightError as e:
            if os.environ.get("CI"):
                raise
            pytest.skip(f"no Chromium to run: {e.message.splitlines()[0]}")
        yield browser
        await browser.close()
