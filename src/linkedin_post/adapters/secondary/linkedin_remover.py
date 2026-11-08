"""PostRemover: delete one of the signed-in user's posts through its "..." menu."""

import re

from patchright.async_api import Page
from patchright.async_api import TimeoutError as PlaywrightTimeoutError

from linkedin_post.adapters.secondary.trace import capture_failure
from linkedin_post.domain.entities import DeleteResult, DeleteStatus, PostRef

_MENU_NAME = re.compile(r"^Open control menu for post", re.I)
_DELETE_NAME = re.compile(r"^Delete", re.I)
# LinkedIn's confirmation button: "Delete", sometimes "Delete post".
_CONFIRM_NAME = re.compile(r"^\s*Delete(\s+post)?\s*$", re.I)


class LinkedInRemover:
    async def delete(self, page: Page, post: PostRef, *, confirm: bool) -> DeleteResult:
        url = post.url
        await page.goto(url, wait_until="domcontentloaded")

        menu_button = page.get_by_role("button", name=_MENU_NAME).first
        try:
            await menu_button.wait_for(state="visible", timeout=20000)
        except PlaywrightTimeoutError:
            return DeleteResult(
                DeleteStatus.POST_NOT_FOUND,
                "The post or its menu did not load.",
                url,
                trace_dir=await capture_failure(page, "delete-post-not-found"),
            )

        await menu_button.click()
        delete_item = page.get_by_role("menuitem", name=_DELETE_NAME).or_(
            page.get_by_role("button", name=re.compile(r"^Delete post", re.I))
        ).first
        try:
            await delete_item.wait_for(state="visible", timeout=5000)
        except PlaywrightTimeoutError:
            await page.keyboard.press("Escape")
            return DeleteResult(
                DeleteStatus.NOT_DELETABLE,
                "The post menu has no Delete item. It is probably not your post.",
                url,
            )

        if not confirm:
            await page.keyboard.press("Escape")
            return DeleteResult(
                DeleteStatus.DRY_RUN,
                "Your post was found and can be deleted. Nothing was deleted.",
                url,
            )

        await delete_item.click()
        # get_by_role matches native <dialog> too; the CSS [role="dialog"] used
        # before did not, which is the same miss create_post had.
        confirm_dialog = (
            page.get_by_role("alertdialog")
            .or_(page.get_by_role("dialog"))
            .filter(has=page.get_by_role("button", name=_CONFIRM_NAME))
            .last
        )
        confirm_button = confirm_dialog.get_by_role("button", name=_CONFIRM_NAME).first
        try:
            await confirm_button.wait_for(state="visible", timeout=10000)
        except PlaywrightTimeoutError:
            trace_dir = await capture_failure(page, "delete-post-confirm-not-found", button_name=_DELETE_NAME)
            await page.keyboard.press("Escape")
            return DeleteResult(
                DeleteStatus.CONFIRM_NOT_FOUND,
                "LinkedIn's confirmation did not appear. Nothing was deleted.",
                url,
                trace_dir=trace_dir,
            )

        await confirm_button.click()
        if await self._gone(page, url, confirm_dialog, menu_button):
            return DeleteResult(DeleteStatus.DELETED, "Post deleted.", url)
        return DeleteResult(
            DeleteStatus.OUTCOME_UNKNOWN,
            "Clicked Delete but could not confirm the post disappeared. Check the post URL.",
            url,
            trace_dir=await capture_failure(page, "delete-post-outcome-unknown"),
        )

    @staticmethod
    async def _gone(page: Page, url: str, confirm_dialog, menu_button) -> bool:
        """True once the post's menu is gone, checked again on a fresh load."""
        try:
            await confirm_dialog.wait_for(state="hidden", timeout=15000)
        except PlaywrightTimeoutError:
            return False
        try:
            await menu_button.wait_for(state="detached", timeout=10000)
            return True
        except PlaywrightTimeoutError:
            pass
        # The page may show other posts whose menus match too: reload the
        # post itself and see whether its menu still comes up.
        await page.goto(url, wait_until="domcontentloaded")
        try:
            await page.get_by_role("button", name=_MENU_NAME).first.wait_for(state="visible", timeout=15000)
        except PlaywrightTimeoutError:
            return True
        return False
