# Copyright (c) 2026 Dmitry Andersson
# SPDX-License-Identifier: MIT
"""LinkedInRemover against a stand-in post page, in a real headless Chromium.

The page mimics LinkedIn's: a "..." menu, a Delete menu item and a native
<dialog> confirmation (no role attribute), which the old CSS locator missed.
"""

import pytest
from patchright.async_api import Browser, Page

from linkedin_post.adapters.secondary.linkedin_remover import LinkedInRemover
from linkedin_post.domain.entities import DeleteStatus, PostRef

pytestmark = pytest.mark.anyio

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
async def page(browser: Browser) -> Page:
    page = await browser.new_page()
    await page.route("**/*", lambda route: route.fulfill(content_type="text/html", body=POST_PAGE))
    return page


async def test_dry_run_finds_delete_and_leaves_post(page: Page) -> None:
    result = await LinkedInRemover().delete(page, REF, confirm=False)
    assert result.status is DeleteStatus.DRY_RUN
    assert await page.locator("#post").count() == 1


async def test_confirms_in_native_dialog_and_deletes(page: Page) -> None:
    result = await LinkedInRemover().delete(page, REF, confirm=True)
    assert result.status is DeleteStatus.DELETED, result
    assert await page.locator("#post").count() == 0
