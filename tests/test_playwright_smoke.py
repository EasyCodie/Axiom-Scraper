import pytest
from playwright.async_api import async_playwright


@pytest.mark.asyncio
async def test_can_open_example():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        try:
            await page.goto("https://example.com", wait_until="domcontentloaded")
            title = await page.title()
            assert "Example Domain" in title
        finally:
            await browser.close()
