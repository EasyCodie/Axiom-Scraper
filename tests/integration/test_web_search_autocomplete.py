"""
Playwright integration tests for search autocomplete functionality.
"""

import pytest
from playwright.async_api import async_playwright, expect


async def _with_page(test_coroutine):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        page = await browser.new_page()
        try:
            await test_coroutine(page)
        finally:
            await browser.close()


@pytest.mark.asyncio
async def test_search_autocomplete_displays_results():
    async def run(page):
        await page.goto('http://localhost:3000')
        await page.wait_for_load_state('networkidle')

        search_input = page.locator('input[placeholder*="Search tokens"]')
        await expect(search_input).to_be_visible()

        await search_input.fill('SOL')
        await page.wait_for_timeout(400)

        popover = page.locator('#search-results')
        await expect(popover).to_be_visible()

    await _with_page(run)


@pytest.mark.asyncio
async def test_search_autocomplete_keyboard_navigation():
    async def run(page):
        await page.goto('http://localhost:3000')
        await page.wait_for_load_state('networkidle')

        search_input = page.locator('input[placeholder*="Search tokens"]')
        await search_input.fill('SOL')
        await page.wait_for_timeout(400)

        await search_input.press('ArrowDown')
        selected = page.locator('[role="option"][aria-selected="true"]')
        await expect(selected).to_be_visible()

        await search_input.press('ArrowDown')
        await search_input.press('Enter')

        await page.wait_for_url('**/token/**', timeout=3000)

    await _with_page(run)


@pytest.mark.asyncio
async def test_search_autocomplete_debounce():
    async def run(page):
        await page.goto('http://localhost:3000')
        await page.wait_for_load_state('networkidle')

        search_input = page.locator('input[placeholder*="Search tokens"]')

        await search_input.fill('S')
        await page.wait_for_timeout(100)
        await search_input.fill('SO')
        await page.wait_for_timeout(100)
        await search_input.fill('SOL')

        await page.wait_for_timeout(400)

        popover = page.locator('#search-results')
        await expect(popover).to_be_visible()

    await _with_page(run)


@pytest.mark.asyncio
async def test_search_autocomplete_shows_loading():
    async def run(page):
        await page.goto('http://localhost:3000')
        await page.wait_for_load_state('networkidle')

        search_input = page.locator('input[placeholder*="Search tokens"]')
        await search_input.fill('TOKEN')

        await page.wait_for_timeout(100)

        popover = page.locator('#search-results')
        await expect(popover).to_be_visible()

    await _with_page(run)


@pytest.mark.asyncio
async def test_search_autocomplete_closes_on_escape():
    async def run(page):
        await page.goto('http://localhost:3000')
        await page.wait_for_load_state('networkidle')

        search_input = page.locator('input[placeholder*="Search tokens"]')
        await search_input.fill('SOL')
        await page.wait_for_timeout(400)

        popover = page.locator('#search-results')
        await expect(popover).to_be_visible()

        await search_input.press('Escape')
        await page.wait_for_timeout(200)

        await expect(popover).not_to_be_visible()

    await _with_page(run)
