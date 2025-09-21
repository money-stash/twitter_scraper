import random
import asyncio
from playwright.async_api import async_playwright

from сonfig import USERNAME, PASSWORD


THRESHOLD = 250_000


def parse_followers(text: str) -> int:
    t = text.lower().replace(",", "").strip()
    num = 0
    for part in t.split():
        if any(ch.isdigit() for ch in part):
            s = part
            mult = 1
            if s.endswith("m"):
                mult = 1_000_000
                s = s[:-1]
            elif s.endswith("k"):
                mult = 1_000
                s = s[:-1]
            try:
                num = int(float(s) * mult)
            except:
                num = 0
            break
    return num


async def extract_usernames_from_spans(page):
    texts = await page.locator("span").all_inner_texts()
    usernames = set()
    for t in texts:
        if "@" in t:
            for part in t.split():
                if "@" in part:
                    u = part[part.find("@") + 1 :]
                    u = "".join(ch for ch in u if ch.isalnum() or ch == "_")
                    if u:
                        usernames.add(u)
    return usernames


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://x.com", wait_until="domcontentloaded")
        await asyncio.sleep(random.uniform(3, 6))

        await page.get_by_test_id("loginButton").first.click()
        await asyncio.sleep(random.uniform(2, 5))

        ui = page.locator('input[autocomplete="username"]')
        await ui.fill(USERNAME)
        await asyncio.sleep(random.uniform(2, 4))
        await ui.press("Enter")
        await asyncio.sleep(random.uniform(3, 6))

        pi = page.locator('input[autocomplete="current-password"]')
        await pi.fill(PASSWORD)
        await asyncio.sleep(random.uniform(3, 6))
        await pi.press("Enter")
        await asyncio.sleep(random.uniform(6, 10))

        await page.goto(
            "https://x.com/realDonaldTrump/followers", wait_until="domcontentloaded"
        )
        await asyncio.sleep(random.uniform(5, 9))

        usernames = set()

        for _ in range(5):
            await page.mouse.wheel(0, 2500)
            await asyncio.sleep(random.uniform(4, 8))

            new_batch = await extract_usernames_from_spans(page)
            usernames |= new_batch

            await asyncio.sleep(random.uniform(2, 5))

        await asyncio.sleep(random.uniform(5, 10))

        for username in usernames:
            try:
                rand_sleep = random.uniform(8, 15)
                await asyncio.sleep(rand_sleep)

                await page.goto(
                    f"https://x.com/{username}", wait_until="domcontentloaded"
                )
                await asyncio.sleep(random.uniform(5, 9))

                link = page.locator(f'a[href="/{username}/verified_followers"]').first
                text = await link.inner_text(timeout=7000)

                print(f"{username}: {text}")
                followers = parse_followers(text)

                await asyncio.sleep(random.uniform(2, 5))

                if followers > THRESHOLD:
                    btn = page.locator('button[aria-label^="Follow"]')
                    if await btn.count() > 0:
                        await asyncio.sleep(random.uniform(2, 4))
                        await btn.first.click()
                        await asyncio.sleep(random.uniform(4, 8))

            except Exception as e:
                print(f"{username}: ERROR {e}")
                await asyncio.sleep(random.uniform(3, 6))

        await asyncio.sleep(random.uniform(5, 10))
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
