import asyncio
from playwright.async_api import async_playwright


async def _fetch(url: str) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
        )
        page = await ctx.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=30_000)
            await page.wait_for_timeout(2_000)
            return await page.content()
        finally:
            await browser.close()


def fetch_page(url: str) -> str:
    """Fetch a URL with a real browser (handles JS-heavy sites)."""
    return asyncio.run(_fetch(url))
