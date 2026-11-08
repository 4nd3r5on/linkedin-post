"""PostRemover: delete one of the signed-in user's posts through its "..." menu."""

import re

from patchright.async_api import Page
from patchright.async_api import TimeoutError as PlaywrightTimeoutError

from linkedin_post.domain.entities import DeleteResult, DeleteStatus, PostRef


class LinkedInRemover:
    async def delete(self, page: Page, post: PostRef, *, confirm: bool) -> DeleteResult:
        url = post.url
        await page.goto(url, wait_until="domcontentloaded")

        menu_button = page.get_by_role(
            "button", name=re.compile(r"^Open control menu for post", re.I)
        ).first
        try:
            await menu_button.wait_for(state="visible", timeout=20000)
        except PlaywrightTimeoutError:
            return DeleteResult(DeleteStatus.POST_NOT_FOUND, "The post or its menu did not load.", url)

        await menu_button.click()
        delete_item = page.get_by_role("menuitem", name=re.compile(r"^Delete", re.I)).or_(
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
        confirm_dialog = page.locator('[role="alertdialog"], [role="dialog"]').filter(
            has=page.get_by_role("button", name="Delete", exact=True)
        ).first
        confirm_button = confirm_dialog.get_by_role("button", name="Delete", exact=True)
        try:
            await confirm_button.wait_for(state="visible", timeout=5000)
        except PlaywrightTimeoutError:
            await page.keyboard.press("Escape")
            return DeleteResult(
                DeleteStatus.CONFIRM_NOT_FOUND,
                "LinkedIn's confirmation did not appear. Nothing was deleted.",
                url,
            )

        await confirm_button.click()
        try:
            await confirm_dialog.wait_for(state="hidden", timeout=15000)
            await menu_button.wait_for(state="detached", timeout=15000)
        except PlaywrightTimeoutError:
            return DeleteResult(
                DeleteStatus.OUTCOME_UNKNOWN,
                "Clicked Delete but could not confirm the post disappeared. Check the post URL.",
                url,
            )
        return DeleteResult(DeleteStatus.DELETED, "Post deleted.", url)
