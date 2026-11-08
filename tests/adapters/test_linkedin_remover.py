"""LinkedInRemover against a stand-in post page, in a real headless Chromium.

The page mimics LinkedIn's: a "..." menu, a Delete menu item and a native
<dialog> confirmation (no role attribute), which the old CSS locator missed.
"""

import os
from pathlib import Path

import pytest
from patchright.async_api import async_playwright

from linkedin_post.adapters.secondary.linkedin_remover import LinkedInRemover
from linkedin_post.domain.entities import DeleteStatus, PostRef

pytestmark = pytest.mark.anyio

_CHROME = Path(
    os.environ.get(
        "LINKEDIN_POST_TEST_CHROME",
        "~/.linkedin-mcp/patchright-browsers/chromium-1248/chrome-linux64/chrome",
    )
).expanduser()

POST_PAGE = """<!doctype html><body>
<article id="post">
  <button aria-label="Open control menu for post by Jane" onclick="menu.hidden=false">...</button>
  <div id="menu" role="menu" hidden>
    <div role="menuitem" tabindex="0" onclick="menu.hidden=true; confirmDialog.showModal()">Delete post</div>
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
async def page():
    if not _CHROME.exists():
        pytest.skip(f"no Chromium at {_CHROME}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=str(_CHROME))
        page = await browser.new_page()
        await page.route("**/*", lambda route: route.fulfill(content_type="text/html", body=POST_PAGE))
        yield page
        await browser.close()


async def test_dry_run_finds_delete_and_leaves_post(page) -> None:
    result = await LinkedInRemover().delete(page, REF, confirm=False)
    assert result.status is DeleteStatus.DRY_RUN
    assert await page.locator("#post").count() == 1


async def test_confirms_in_native_dialog_and_deletes(page) -> None:
    result = await LinkedInRemover().delete(page, REF, confirm=True)
    assert result.status is DeleteStatus.DELETED, result
    assert await page.locator("#post").count() == 0
