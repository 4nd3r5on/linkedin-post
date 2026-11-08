"""PostComposer: drive LinkedIn's share dialog in the browser page upstream owns."""

import logging
import re

from patchright.async_api import Locator, Page
from patchright.async_api import TimeoutError as PlaywrightTimeoutError

from linkedin_post.adapters.secondary.trace import capture_failure
from linkedin_post.common.linkedin import SHARE_URL, absolute_url
from linkedin_post.domain.entities import PostText, PublishResult, PublishStatus

logger = logging.getLogger(__name__)

# Any editable element. The share box may have no role="textbox" or Quill class,
# so the dialog it sits in is what pins it down.
EDITOR = '[contenteditable]:not([contenteditable="false"])'

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
    await page.keyboard.press("Escape")
    discard = page.get_by_role("button", name="Discard", exact=True)
    try:
        await discard.click(timeout=5000)
    except PlaywrightTimeoutError:
        pass
    try:
        await dialog.wait_for(state="hidden", timeout=5000)
    except PlaywrightTimeoutError:
        logger.warning("share dialog still open after discard")


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
        return True
    except PlaywrightTimeoutError:
        logger.info("shareActive did not open the dialog; clicking Start a post")
    start = page.get_by_role("button", name=re.compile(r"^Start a post", re.I)).or_(
        page.get_by_text("Start a post", exact=True)
    ).first
    try:
        await start.click(timeout=15000)
        await editor.wait_for(state="visible", timeout=15000)
        return True
    except PlaywrightTimeoutError:
        return False


class LinkedInComposer:
    async def publish(self, page: Page, text: PostText, *, confirm: bool) -> PublishResult:
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
        inserted = await editor.evaluate(_INSERT_JS, text.value)
        if inserted != "written":
            trace_dir = await capture_failure(page, "create-post-insert-failed", {"insert": inserted})
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
                "Text inserted, then the draft was discarded. Nothing was posted.",
                visibility=visibility,
                characters=len(text),
            )

        post_button = dialog.get_by_role("button", name="Post", exact=True)
        try:
            await post_button.wait_for(state="visible", timeout=5000)
            problem = None if await post_button.is_enabled() else "Post button stayed disabled."
        except PlaywrightTimeoutError:
            problem = "Post button not found."
        if problem is not None:
            await _discard(page, dialog)
            return PublishResult(PublishStatus.INSERT_FAILED, problem, visibility=visibility)

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
        )
