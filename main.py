import random
import asyncio
from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
)

from utils.mini_utils import parse_followers, extract_usernames_from_spans, short_sleep
from сonfig import USERNAME, PASSWORD, NICKNAME


THRESHOLD = 250_000


async def login(page):
    await page.goto("https://x.com", wait_until="domcontentloaded")

    await asyncio.sleep(1)

    await short_sleep(0.4, 0.9)

    await page.get_by_test_id("loginButton").first.click()
    await page.wait_for_selector('input[autocomplete="username"]', timeout=15000)

    ui = page.locator('input[autocomplete="username"]')

    await ui.fill(USERNAME)
    await ui.press("Enter")
    await page.wait_for_selector(
        'input[autocomplete="current-password"]', timeout=15000
    )
    pi = page.locator('input[autocomplete="current-password"]')
    await pi.fill(PASSWORD)
    await pi.press("Enter")

    # input("Press Enter after completing any CAPTCHA or 2FA...")

    try:
        await page.wait_for_selector(
            '[data-testid="SideNav_AccountSwitcher_Button"], a[aria-label="Profile"]',
            timeout=20000,
        )
    except PlaywrightTimeoutError:
        await page.wait_for_selector(
            'nav[role="navigation"], [data-testid="primaryColumn"]', timeout=20000
        )


async def collect_usernames(page):
    await page.goto(
        "https://x.com/realDonaldTrump/followers", wait_until="domcontentloaded"
    )
    await page.wait_for_selector('div[role="list"]', timeout=20000)

    await asyncio.sleep(1)

    usernames = set()
    for _ in range(10):
        await page.mouse.wheel(0, 3500)
        await short_sleep(0.5, 1.2)
        new_batch = await extract_usernames_from_spans(page)
        usernames |= new_batch
    return usernames


async def follow_users(page, usernames, threshold=THRESHOLD):
    for username in usernames:
        try:
            await short_sleep(0.9, 1.8)
            await page.goto(f"https://x.com/{username}", wait_until="domcontentloaded")

            await asyncio.sleep(1)

            await page.wait_for_selector('a[href$="/verified_followers"]', timeout=7000)
            link = page.locator(f'a[href="/{username}/verified_followers"]').first
            text = await link.inner_text(timeout=7000)
            print(f"{username}: {text}")
            followers = parse_followers(text)
            if followers > threshold:
                btn = page.locator('button[aria-label^="Follow"]')
                if await btn.count() > 0:
                    await short_sleep(0.3, 0.7)
                    await btn.first.click()
                    await short_sleep(0.6, 1.1)
        except Exception as e:
            print(f"{username}: ERROR {e}")
            await short_sleep(0.7, 1.4)


async def click_confirm_unfollow(page):
    try:
        confirm = page.locator('[data-testid="confirmationSheetConfirm"]').first
        await confirm.wait_for(state="visible", timeout=4000)
        await short_sleep(0.25, 0.6)
        await confirm.click(timeout=4000)
        await short_sleep(0.6, 1.2)
        return True
    except PlaywrightTimeoutError:
        pass
    try:
        dialog = page.locator('div[role="dialog"]').first
        await dialog.wait_for(state="visible", timeout=3000)
        btn = dialog.locator('span:has-text("Unfollow")').first
        await btn.wait_for(state="visible", timeout=3000)
        await short_sleep(0.25, 0.6)
        await btn.click(timeout=3000)
        await short_sleep(0.6, 1.2)
        return True
    except PlaywrightTimeoutError:
        pass
    try:
        menu_btn = page.locator('div[role="menu"] span:has-text("Unfollow")').first
        await menu_btn.wait_for(state="visible", timeout=3000)
        await short_sleep(0.25, 0.6)
        await menu_btn.click(timeout=3000)
        await short_sleep(0.6, 1.2)
        return True
    except PlaywrightTimeoutError:
        return False


async def unfollow_users(page):
    await page.goto(
        f"https://x.com/{NICKNAME}/following", wait_until="domcontentloaded"
    )
    try:
        timeline = page.locator('div[aria-label="Timeline: Following"]').first
        await timeline.wait_for(state="visible", timeout=15000)
    except PlaywrightTimeoutError:
        timeline = page.locator('div[role="region"][aria-label^="Timeline:"]').first
        await timeline.wait_for(state="visible", timeout=15000)

    processed_any = True
    while processed_any:
        processed_any = False
        spans = timeline.locator('span:has-text("Following")')
        count = await spans.count()
        if count == 0:
            await page.mouse.wheel(0, 2500)
            await short_sleep(0.6, 1.2)
            spans = timeline.locator('span:has-text("Following")')
            count = await spans.count()
            if count == 0:
                break

        for i in range(count):
            try:
                el = spans.nth(i)
                await el.scroll_into_view_if_needed(timeout=7000)
                await short_sleep(0.35, 0.8)
                handle = await el.element_handle()
                await el.click(timeout=7000)
                await short_sleep(0.5, 1.1)
                await click_confirm_unfollow(page)
                try:
                    if handle:
                        await page.wait_for_function(
                            "(e) => !e || ((e.innerText || '').trim() !== 'Following')",
                            arg=handle,
                            timeout=5000,
                        )
                except PlaywrightTimeoutError:
                    pass
                processed_any = True
            except Exception as e:
                print(f"UNFOLLOW ERROR: {e}")
                await short_sleep(0.7, 1.3)

        await page.mouse.wheel(0, 3000)
        await short_sleep(0.8, 1.6)


async def click_confirm_repost(page):
    try:
        confirm = page.locator('[data-testid="retweetConfirm"]').first
        await confirm.wait_for(state="visible", timeout=3000)
        await short_sleep(0.25, 0.6)
        await confirm.click(timeout=3000)
        await short_sleep(0.6, 1.1)
        return True
    except PlaywrightTimeoutError:
        pass
    try:
        dialog = page.locator('div[role="dialog"]').first
        await dialog.wait_for(state="visible", timeout=2000)
        btn = dialog.locator('span:has-text("Repost")').first
        await btn.wait_for(state="visible", timeout=2000)
        await short_sleep(0.25, 0.6)
        await btn.click(timeout=2000)
        await short_sleep(0.6, 1.1)
        return True
    except PlaywrightTimeoutError:
        return False


async def repost_posts(page, target="realDonaldTrump", times=3):
    await page.goto(f"https://x.com/{target}", wait_until="domcontentloaded")
    await page.wait_for_selector('[data-testid="primaryColumn"]', timeout=15000)
    done = 0
    while done < times:
        buttons = page.locator(
            '[data-testid="retweet"], button[aria-label*="Repost"], div[role="button"][aria-label*="Repost"]'
        )
        count = await buttons.count()
        if count == 0:
            await page.mouse.wheel(0, 3000)
            await short_sleep(0.7, 1.3)
            continue
        progressed = False
        for i in range(count):
            if done >= times:
                break
            btn = buttons.nth(i)
            try:
                await btn.scroll_into_view_if_needed(timeout=6000)
                await short_sleep(0.35, 0.8)
                label = (await btn.get_attribute("aria-label")) or ""
                if "Repost" not in label:
                    continue
                await btn.click(timeout=6000)
                await short_sleep(0.4, 0.9)
                if await click_confirm_repost(page):
                    done += 1
                    progressed = True
                    await short_sleep(0.9, 1.7)
                else:
                    await page.keyboard.press("Escape")
                    await short_sleep(0.5, 1.0)
                    await page.mouse.wheel(0, 2500)
                    await short_sleep(0.7, 1.3)
            except Exception:
                await short_sleep(0.6, 1.2)
        if not progressed:
            await page.mouse.wheel(0, 3500)
            await short_sleep(0.8, 1.4)


async def main():
    while True:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await p.chromium.launch_persistent_context(
                user_data_dir="/tmp/x_ud", headless=False
            )
            page = await context.new_page()

            await login(page)
            users = await collect_usernames(page)
            await follow_users(page, users)
            await unfollow_users(page)
            await repost_posts(page, target="realDonaldTrump", times=3)

            await context.close()
            await browser.close()
            await asyncio.sleep(45)


if __name__ == "__main__":
    asyncio.run(main())
