# Copyright (c) 2026 Dmitry Andersson
# SPDX-License-Identifier: MIT
"""PostComposer: drive LinkedIn's share dialog in the browser page upstream owns."""

import asyncio
import contextlib
import logging
import re
from typing import override

from patchright.async_api import Error as PlaywrightError
from patchright.async_api import Locator, Page
from patchright.async_api import TimeoutError as PlaywrightTimeoutError

from linkedin_post.adapters.secondary.trace import capture_failure
from linkedin_post.common.linkedin import SHARE_URL, absolute_url
from linkedin_post.domain.entities import PostMedia, PostText, PublishResult, PublishStatus
from linkedin_post.domain.ports.secondary.linkedin import PostComposer

logger = logging.getLogger(__name__)

# Any editable element. The share box may have no role="textbox" or Quill class,
# so the dialog it sits in is what pins it down.
EDITOR = '[contenteditable]:not([contenteditable="false"])'

# The share box's media button: "Add media", "Add a photo", "Photo"...
MEDIA_BUTTON = re.compile(r"^(add (a )?)?(media|photo|image)", re.IGNORECASE)
# Uploads of up to 20 images of 5 MB each can take a while.
UPLOAD_TIMEOUT_MS = 90_000

# Adapted from upstream message_sender.py (Apache-2.0): focus the empty editor
# and insert the whole text with execCommand('insertText'), which yields one <p>
# per line (blank lines kept) the way LinkedIn's own editor builds them. Called
# through a locator, so `editor` is the element even inside a shadow root.
_INSERT_JS = """(editor, text) => {
    if ((editor.innerText || '').replace(/\\s+/g, ' ').trim()) return 'occupied';
    editor.focus();
    if (document.activeElement !== editor) return 'unfocused';
    if (
        typeof document.queryCommandSupported !== 'function' ||
        !document.queryCommandSupported('insertText')
    ) return 'unsupported';
    if (document.execCommand('insertText', false, text) !== true) return 'unsupported';
    const norm = (s) => s.replace(/\\u00a0/g, ' ').replace(/\\s+/g, ' ').trim();
    return norm(editor.innerText || '') === norm(text) ? 'written' : 'mismatch';
}"""


async def _visibility(dialog: Locator) -> str | None:
    button = dialog.get_by_role("button", name="Post to", exact=False).first
    try:
        label = (await button.inner_text(timeout=3000)).strip()
    except PlaywrightTimeoutError:
        return None
    return label.removeprefix("Post to").strip() or label


async def _discard(page: Page, dialog: Locator) -> None:
    """Escape and confirm Discard, again if the image editor sat on top."""
    discard = page.get_by_role("button", name="Discard", exact=True)
    for _ in range(3):
        await page.keyboard.press("Escape")
        with contextlib.suppress(PlaywrightTimeoutError):
            await discard.click(timeout=3000)
        with contextlib.suppress(PlaywrightTimeoutError):
            await dialog.wait_for(state="hidden", timeout=3000)
        if await page.get_by_role("dialog").count() == 0:
            return
    logger.warning("share dialog still open after discard")


async def _wait_enabled(button: Locator, timeout_ms: int) -> bool:
    try:
        await button.wait_for(state="visible", timeout=min(timeout_ms, 5000))
    except PlaywrightTimeoutError:
        return False
    for _ in range(timeout_ms // 500):
        if await button.is_enabled():
            return True
        await asyncio.sleep(0.5)
    return False


async def _attach(page: Page, dialog: Locator, media: PostMedia) -> str | None:
    """Pick the files through the media button, then leave the image editor.

    Returns what went wrong, or None once the composer is back with the images.
    """
    files = [str(path) for path in media.paths]
    button = dialog.get_by_role("button", name=MEDIA_BUTTON).first
    try:
        async with page.expect_file_chooser(timeout=15000) as chooser_info:
            await button.click(timeout=10000)
        chooser = await chooser_info.value
    except PlaywrightTimeoutError:
        # No chooser: fall back to the file input the share box renders.
        logger.info("no file chooser from the media button; trying the file input")
        try:
            await page.locator('input[type="file"]').first.set_input_files(files, timeout=5000)
        except PlaywrightTimeoutError:
            return "No media button or file input in the share dialog."
        except PlaywrightError as e:
            return f"The file input refused the images: {e.message.splitlines()[0]}"
    else:
        if len(files) > 1 and not chooser.is_multiple():
            return "LinkedIn's file picker takes only one image."
        await chooser.set_files(files)

    # The image editor (crop, ALT) comes up on top; Next returns to the composer
    # and stays disabled while the images upload.
    next_button = page.get_by_role("dialog").get_by_role("button", name="Next", exact=True).first
    if not await _wait_enabled(next_button, UPLOAD_TIMEOUT_MS):
        return "LinkedIn's image editor did not accept the images."
    await next_button.click()
    try:
        await dialog.locator(EDITOR).first.wait_for(state="visible", timeout=15000)
    except PlaywrightTimeoutError:
        return "The share dialog did not come back after the image editor."
    return None


async def _find_post_url(page: Page) -> str | None:
    link = page.get_by_role("link", name="View post").first
    try:
        href = await link.get_attribute("href", timeout=8000)
    except PlaywrightTimeoutError:
        return None
    return absolute_url(href) if href else None


async def _open_share_dialog(page: Page, editor: Locator) -> bool:
    """Try ?shareActive=true first, then click "Start a post" like a user would."""
    await page.goto(SHARE_URL, wait_until="domcontentloaded")
    try:
        await editor.wait_for(state="visible", timeout=8000)
    except PlaywrightTimeoutError:
        logger.info("shareActive did not open the dialog; clicking Start a post")
    else:
        return True
    start = (
        page.get_by_role("button", name=re.compile(r"^Start a post", re.IGNORECASE))
        .or_(page.get_by_text("Start a post", exact=True))
        .first
    )
    try:
        await start.click(timeout=15000)
        await editor.wait_for(state="visible", timeout=15000)
    except PlaywrightTimeoutError:
        return False
    return True


async def _click_post(
    page: Page, dialog: Locator, media: PostMedia, visibility: str | None
) -> PublishResult:
    """Wait for Post to enable (uploads finishing), click it, see the dialog close."""
    post_button = dialog.get_by_role("button", name="Post", exact=True)
    if not await _wait_enabled(post_button, UPLOAD_TIMEOUT_MS if media else 5000):
        trace_dir = await capture_failure(page, "create-post-button-disabled")
        await _discard(page, dialog)
        return PublishResult(
            PublishStatus.INSERT_FAILED,
            "Post button missing or disabled; nothing was posted.",
            visibility=visibility,
            trace_dir=trace_dir,
        )

    await post_button.click()
    # From here a retry could publish twice.
    try:
        await dialog.wait_for(state="hidden", timeout=20000)
    except PlaywrightTimeoutError:
        return PublishResult(
            PublishStatus.OUTCOME_UNKNOWN,
            "Clicked Post but the dialog did not close. Check the feed before retrying.",
            visibility=visibility,
        )
    return PublishResult(
        PublishStatus.POSTED,
        "Post published.",
        visibility=visibility,
        post_url=await _find_post_url(page),
        images=len(media) or None,
    )


def _and_images(media: PostMedia) -> str:
    return f" and {len(media)} image(s) attached" if media else ""


class LinkedInComposer(PostComposer):
    """Publishes through the share dialog of the page upstream signed in."""

    @override
    async def publish(
        self, page: Page, text: PostText, media: PostMedia, *, confirm: bool
    ) -> PublishResult:
        # get_by_role also matches a native <dialog>, which [role="dialog"] misses.
        dialog = page.get_by_role("dialog").filter(has=page.locator(EDITOR)).first
        editor = dialog.locator(EDITOR).first
        if not await _open_share_dialog(page, editor):
            return PublishResult(
                PublishStatus.EDITOR_NOT_FOUND,
                "LinkedIn's share dialog did not open. Nothing was posted.",
                url=page.url,
                trace_dir=await capture_failure(page, "create-post-editor-not-found"),
            )

        visibility = await _visibility(dialog)
        if media and (problem := await _attach(page, dialog, media)) is not None:
            trace_dir = await capture_failure(
                page, "create-post-media-rejected", {"problem": problem, "images": len(media)}
            )
            await _discard(page, dialog)
            return PublishResult(
                PublishStatus.MEDIA_REJECTED,
                f"{problem} Nothing was posted.",
                visibility=visibility,
                trace_dir=trace_dir,
            )

        inserted = await editor.evaluate(_INSERT_JS, text.value) if text.value else "written"
        if inserted != "written":
            trace_dir = await capture_failure(
                page, "create-post-insert-failed", {"insert": inserted}
            )
            await _discard(page, dialog)
            return PublishResult(
                PublishStatus.INSERT_FAILED,
                f"Could not insert the text ({inserted}); nothing was posted.",
                visibility=visibility,
                trace_dir=trace_dir,
            )

        if not confirm:
            await _discard(page, dialog)
            return PublishResult(
                PublishStatus.DRY_RUN,
                f"Text inserted{_and_images(media)}, then the draft was discarded. "
                "Nothing was posted.",
                visibility=visibility,
                characters=len(text),
                images=len(media) or None,
            )

        return await _click_post(page, dialog, media, visibility)
