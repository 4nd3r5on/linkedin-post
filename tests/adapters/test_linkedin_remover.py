# Copyright (c) 2026 Dmitry Andersson
# SPDX-License-Identifier: MIT
"""LinkedInRemover against a stand-in post page, in a real headless Chromium.

The page mimics LinkedIn's: a "..." menu, a Delete menu item and a native
<dialog> confirmation (no role attribute), which the old CSS locator missed.
"""

import os
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from patchright.async_api import Error as PlaywrightError
from patchright.async_api import Page, async_playwright

from linkedin_post.adapters.secondary.linkedin_remover import LinkedInRemover
from linkedin_post.domain.entities import DeleteStatus, PostRef

pytestmark = pytest.mark.anyio

# LINKEDIN_POST_TEST_CHROME, else upstream's managed Chromium, else patchright's
# own (`patchright install chromium`, as CI does).
_UPSTREAM_CHROME = "~/.linkedin-mcp/patchright-browsers/chromium-1248/chrome-linux64/chrome"
_CHROME = Path(os.environ.get("LINKEDIN_POST_TEST_CHROME", _UPSTREAM_CHROME)).expanduser()

POST_PAGE = """<!doctype html><body>
<article id="post">
  <button aria-label="Open control menu for post by Jane" onclick="menu.hidden=false">...</button>
  <div id="menu" role="menu" hidden>
    <div role="menuitem" tabindex="0"
         onclick="menu.hidden=true; confirmDialog.showModal()">Delete post</div>
  </div>
  <p>Hello</p>
</article>
<dialog id="confirmDialog"><h2>Delete post?</h2>
  <button onclick="confirmDialog.close()">Cancel</button>
  <button onclick="confirmDialog.close(); post.remove()">Delete</button>
</dialog>
<script>const menu = document.getElementById('menu');</script>
</body>"""

REF = PostRef.parse("urn:li:activity:7525284009694609408")


@pytest.fixture
async def page() -> AsyncIterator[Page]:
    executable = str(_CHROME) if _CHROME.exists() else None
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True, executable_path=executable)
        except PlaywrightError as e:
            if os.environ.get("CI"):
                raise
            pytest.skip(f"no Chromium to run: {e.message.splitlines()[0]}")
        page = await browser.new_page()
        await page.route(
            "**/*", lambda route: route.fulfill(content_type="text/html", body=POST_PAGE)
        )
        yield page
        await browser.close()


async def test_dry_run_finds_delete_and_leaves_post(page: Page) -> None:
    result = await LinkedInRemover().delete(page, REF, confirm=False)
    assert result.status is DeleteStatus.DRY_RUN
    assert await page.locator("#post").count() == 1


async def test_confirms_in_native_dialog_and_deletes(page: Page) -> None:
    result = await LinkedInRemover().delete(page, REF, confirm=True)
    assert result.status is DeleteStatus.DELETED, result
    assert await page.locator("#post").count() == 0
