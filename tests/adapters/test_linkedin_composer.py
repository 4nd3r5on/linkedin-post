# Copyright (c) 2026 Dmitry Andersson
# SPDX-License-Identifier: MIT
"""LinkedInComposer against a stand-in share dialog, in a real headless Chromium.

The page mimics LinkedIn's flow for images: the composer's media button opens
a file picker, an image editor replaces the composer, and its Next button
(disabled while "uploading") brings the composer back.
"""

import json
from pathlib import Path

import pytest
from patchright.async_api import Browser, Page

from linkedin_post.adapters.secondary.linkedin_composer import LinkedInComposer
from linkedin_post.domain.entities import PostMedia, PostText, PublishStatus

pytestmark = pytest.mark.anyio

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16

SHARE_PAGE = """<!doctype html><body>
<dialog id="composer">
  <button>Post to Anyone</button>
  <div id="editor" contenteditable="true"></div>
  <div id="thumbs"></div>
  <button aria-label="Add media" onclick="picker.click()">Media</button>
  <input id="picker" type="file" MULTIPLE hidden>
  <button onclick="post()">Post</button>
</dialog>
<dialog id="mediaEditor"><h2>Editor</h2><button id="next" disabled>Next</button></dialog>
<script>
  const [composer, mediaEditor, picker, next] =
    ['composer', 'mediaEditor', 'picker', 'next'].map((id) => document.getElementById(id));
  let picked = [];
  const post = () => {
    const posted = {text: editor.innerText, images: thumbs.children.length};
    document.body.dataset.posted = JSON.stringify(posted);
    composer.close();
  };
  composer.showModal();
  picker.onchange = () => {
    picked = [...picker.files].map((f) => f.name);
    document.body.dataset.picked = JSON.stringify(picked);
    composer.close();
    mediaEditor.showModal();
    setTimeout(() => { next.disabled = false; }, 300);
  };
  next.onclick = () => {
    for (const name of picked) thumbs.append(Object.assign(new Image(), {alt: name}));
    mediaEditor.close();
    composer.showModal();
  };
</script>
</body>"""


async def _data(page: Page, key: str) -> object:
    raw = await page.locator("body").get_attribute(f"data-{key}")
    return None if raw is None else json.loads(raw)


async def _page(browser: Browser, html: str) -> Page:
    page = await browser.new_page()
    await page.route("**/*", lambda route: route.fulfill(content_type="text/html", body=html))
    return page


@pytest.fixture
def media(tmp_path: Path) -> PostMedia:
    paths = []
    for name in ("a.png", "b.png"):
        path = tmp_path / name
        path.write_bytes(PNG)
        paths.append(str(path))
    return PostMedia.parse(paths)


async def test_posts_text_with_images(browser: Browser, media: PostMedia) -> None:
    page = await _page(browser, SHARE_PAGE)
    result = await LinkedInComposer().publish(page, PostText.parse("hi"), media, confirm=True)
    assert result.status is PublishStatus.POSTED, result
    assert result.images == 2
    assert await _data(page, "posted") == {"text": "hi", "images": 2}


async def test_dry_run_attaches_then_discards(browser: Browser, media: PostMedia) -> None:
    page = await _page(browser, SHARE_PAGE)
    result = await LinkedInComposer().publish(page, PostText.parse("hi"), media, confirm=False)
    assert result.status is PublishStatus.DRY_RUN, result
    assert await _data(page, "picked") == ["a.png", "b.png"]
    assert await _data(page, "posted") is None
    assert await page.get_by_role("dialog").count() == 0


async def test_image_only_post(browser: Browser, media: PostMedia) -> None:
    page = await _page(browser, SHARE_PAGE)
    text = PostText.parse("", allow_blank=True)
    result = await LinkedInComposer().publish(page, text, media, confirm=True)
    assert result.status is PublishStatus.POSTED, result
    assert await _data(page, "posted") == {"text": "", "images": 2}


async def test_single_file_picker_rejects_several_images(
    browser: Browser, media: PostMedia
) -> None:
    page = await _page(browser, SHARE_PAGE.replace(" MULTIPLE", ""))
    result = await LinkedInComposer().publish(page, PostText.parse("hi"), media, confirm=True)
    assert result.status is PublishStatus.MEDIA_REJECTED, result
    assert result.retry_safe
    assert await _data(page, "posted") is None
