import asyncio, random


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


async def short_sleep(a=0.3, b=0.8):
    await asyncio.sleep(random.uniform(a, b))
