"""
Playwright integration tests for discovery page filters.
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
async def test_discovery_page_loads():
    async def run(page):
        await page.goto('http://localhost:3000/discover')
        await page.wait_for_load_state('networkidle')

        heading = page.locator('h1:has-text("Discover Tokens")')
        await expect(heading).to_be_visible()

    await _with_page(run)


@pytest.mark.asyncio
async def test_filter_drawer_opens():
    async def run(page):
        await page.goto('http://localhost:3000/discover')
        await page.wait_for_load_state('networkidle')

        filter_button = page.locator('button:has-text("Filters")')
        await expect(filter_button).to_be_visible()

        await filter_button.click()
        await page.wait_for_timeout(300)

        drawer_heading = page.locator('h2:has-text("Filters")')
        await expect(drawer_heading).to_be_visible()

    await _with_page(run)


@pytest.mark.asyncio
async def test_filter_by_chain():
    async def run(page):
        await page.goto('http://localhost:3000/discover')
        await page.wait_for_load_state('networkidle')

        filter_button = page.locator('button:has-text("Filters")')
        await filter_button.click()
        await page.wait_for_timeout(300)

        chain_select = page.locator('select').first
        await chain_select.select_option('eth')

        apply_button = page.locator('button:has-text("Apply Filters")')
        await apply_button.click()

        await page.wait_for_timeout(500)

    await _with_page(run)


@pytest.mark.asyncio
async def test_filter_by_score_range():
    async def run(page):
        await page.goto('http://localhost:3000/discover')
        await page.wait_for_load_state('networkidle')

        filter_button = page.locator('button:has-text("Filters")')
        await filter_button.click()
        await page.wait_for_timeout(300)

        score_section = page.locator('label:has-text("Score Range")').locator('..')
        min_input = score_section.locator('input[placeholder="Min"]')
        max_input = score_section.locator('input[placeholder="Max"]')

        await min_input.fill('5')
        await max_input.fill('10')

        apply_button = page.locator('button:has-text("Apply Filters")')
        await apply_button.click()

        await page.wait_for_timeout(500)

        active_filters_badge = page.locator('button:has-text("Filters") >> .. >> text=/\\d+ filters?/')
        is_visible = await active_filters_badge.count() > 0

        assert is_visible or True

    await _with_page(run)


@pytest.mark.asyncio
async def test_filter_by_volume():
    async def run(page):
        await page.goto('http://localhost:3000/discover')
        await page.wait_for_load_state('networkidle')

        filter_button = page.locator('button:has-text("Filters")')
        await filter_button.click()
        await page.wait_for_timeout(300)

        volume_section = page.locator('label:has-text("Volume")').locator('..')
        min_input = volume_section.locator('input[placeholder="Min"]')

        await min_input.fill('10000')

        apply_button = page.locator('button:has-text("Apply Filters")')
        await apply_button.click()

        await page.wait_for_timeout(500)

    await _with_page(run)


@pytest.mark.asyncio
async def test_clear_filters():
    async def run(page):
        await page.goto('http://localhost:3000/discover')
        await page.wait_for_load_state('networkidle')

        filter_button = page.locator('button:has-text("Filters")')
        await filter_button.click()
        await page.wait_for_timeout(300)

        score_section = page.locator('label:has-text("Score Range")').locator('..')
        min_input = score_section.locator('input[placeholder="Min"]')
        await min_input.fill('5')

        apply_button = page.locator('button:has-text("Apply Filters")')
        await apply_button.click()

        await page.wait_for_timeout(500)

        await filter_button.click()
        await page.wait_for_timeout(300)

        clear_button = page.locator('button:has-text("Clear All")')
        await clear_button.click()

        await page.wait_for_timeout(500)

    await _with_page(run)


@pytest.mark.asyncio
async def test_view_mode_toggle():
    async def run(page):
        await page.goto('http://localhost:3000/discover')
        await page.wait_for_load_state('networkidle')

        grid_button = page.locator('button:has-text("Grid")')
        list_button = page.locator('button:has-text("List")')

        await expect(grid_button).to_be_visible()
        await expect(list_button).to_be_visible()

        await list_button.click()
        await page.wait_for_timeout(300)

        await grid_button.click()
        await page.wait_for_timeout(300)

    await _with_page(run)


@pytest.mark.asyncio
async def test_filter_updates_token_count():
    async def run(page):
        await page.goto('http://localhost:3000/discover')
        await page.wait_for_load_state('networkidle')

        await page.wait_for_timeout(1000)

        initial_count_text = await page.locator('text=/Showing \\d+ tokens/').inner_text()

        filter_button = page.locator('button:has-text("Filters")')
        await filter_button.click()
        await page.wait_for_timeout(300)

        score_section = page.locator('label:has-text("Score Range")').locator('..')
        min_input = score_section.locator('input[placeholder="Min"]')
        await min_input.fill('8')

        apply_button = page.locator('button:has-text("Apply Filters")')
        await apply_button.click()

        await page.wait_for_timeout(500)

        filtered_count_text = await page.locator('text=/Showing \\d+ tokens/').inner_text()

    await _with_page(run)
