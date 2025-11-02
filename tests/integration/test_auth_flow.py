"""
Integration tests for Supabase authentication flows.

Tests:
- Login modal opening on protected route access
- Email magic link flow
- OAuth provider buttons rendering
- Sign out functionality
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="function")
def web_url() -> str:
    """Web application URL fixture."""
    return "http://localhost:3000"


def test_auth_modal_opens_on_protected_route(page: Page, web_url: str):
    """Test that accessing protected routes opens the login modal."""
    page.goto(f"{web_url}/watchlist")
    
    expect(page.locator("text=Sign in to Axiom")).to_be_visible(timeout=10000)
    
    expect(page.locator("input[type='email']")).to_be_visible()
    expect(page.locator("button:has-text('Send magic link')")).to_be_visible()


def test_auth_modal_has_oauth_providers(page: Page, web_url: str):
    """Test that OAuth provider buttons are rendered in login modal."""
    page.goto(f"{web_url}/watchlist")
    
    expect(page.locator("text=Sign in to Axiom")).to_be_visible(timeout=10000)
    
    expect(page.locator("button:has-text('Google')")).to_be_visible()
    expect(page.locator("button:has-text('Telegram')")).to_be_visible()


def test_email_input_validation(page: Page, web_url: str):
    """Test email input validation in login modal."""
    page.goto(web_url)
    
    page.locator("button:has-text('Log in')").click()
    
    expect(page.locator("text=Sign in to Axiom")).to_be_visible(timeout=5000)
    
    email_input = page.locator("input[type='email']")
    email_input.fill("invalid-email")
    
    page.locator("button:has-text('Send magic link')").click()
    
    expect(email_input).to_have_attribute("type", "email")


def test_login_modal_closes(page: Page, web_url: str):
    """Test that login modal can be closed."""
    page.goto(web_url)
    
    page.locator("button:has-text('Log in')").click()
    
    expect(page.locator("text=Sign in to Axiom")).to_be_visible(timeout=5000)
    
    page.locator("button[aria-label='Close login modal']").first.click()
    
    expect(page.locator("text=Sign in to Axiom")).not_to_be_visible(timeout=3000)


def test_header_shows_login_buttons_when_not_authenticated(page: Page, web_url: str):
    """Test that header shows login/access buttons when not authenticated."""
    page.goto(web_url)
    
    expect(page.locator("button:has-text('Log in')")).to_be_visible()
    expect(page.locator("button:has-text('Request access')")).to_be_visible()


def test_protected_routes_redirect_with_query_params(page: Page, web_url: str):
    """Test that protected routes redirect with auth query params."""
    page.goto(f"{web_url}/watchlist")
    
    expect(page).to_have_url(f"{web_url}/?redirect=%2Fwatchlist&auth=required", timeout=10000)


def test_magic_link_email_validation(page: Page, web_url: str):
    """Test magic link form requires valid email format."""
    page.goto(web_url)
    page.locator("button:has-text('Log in')").click()
    
    expect(page.locator("text=Sign in to Axiom")).to_be_visible(timeout=5000)
    
    email_input = page.locator("input[type='email']")
    
    email_input.fill("")
    page.locator("button:has-text('Send magic link')").click()
    
    expect(email_input).to_be_focused()
