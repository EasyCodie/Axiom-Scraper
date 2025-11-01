"""
Authentication setup script for Axiom.

This script opens a browser so you can log in to Axiom with Google OAuth.
Your session will be saved to storage_state.json for reuse by the scraper.

Usage:
    python scripts/setup_auth.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Optional, Any

from playwright.async_api import async_playwright


async def setup_authentication(
    url: str = "https://axiom.trade",
    storage_state_path: str = "storage_state.json",
    browser_channel: Optional[str] = "chrome",
) -> None:
    """
    Launch a browser for manual Google OAuth login and save the session state.

    Args:
        url: Axiom URL to open for authentication.
        storage_state_path: Destination file for the Playwright storage state.
        browser_channel: The Playwright browser channel (for Chrome pass "chrome").
    """
    print("=" * 60)
    print("Axiom Authentication Setup")
    print("=" * 60)
    print("\nThis will open a browser window where you can log in to Axiom.")
    print("After logging in successfully, return to this terminal.")
    print("\nYour session will be saved to:", storage_state_path)
    input("\nPress Enter to continue or Ctrl+C to cancel...")

    async with async_playwright() as playwright:
        print("\n[1/3] Launching browser...")
        launch_kwargs: dict[str, Any] = {"headless": False}

        if browser_channel:
            launch_kwargs["channel"] = browser_channel

        try:
            browser = await playwright.chromium.launch(**launch_kwargs)
        except Exception as launch_error:
            if browser_channel:
                print(
                    f"[warning] Failed to launch channel '{browser_channel}': {launch_error}"
                )
                print("[warning] Falling back to the bundled Chromium build.")
                browser = await playwright.chromium.launch(headless=False)
            else:
                raise

        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )

        print("[2/3] Opening Axiom login page...")
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            print("\n" + "=" * 60)
            print("PLEASE LOG IN TO AXIOM IN THE BROWSER WINDOW")
            print("=" * 60)
            print("\nInstructions:")
            print("1. Click the Google login button.")
            print("2. Complete the Google OAuth flow.")
            print("3. Wait until you see the Axiom dashboard.")
            print("4. Return to this terminal before closing the browser.")
            input("\nPress Enter here once you are logged in and see the dashboard...")
        except Exception as error:
            print(f"\n[warning] Encountered an error while loading the page: {error}")
            print("If you've finished logging in, the session may still be saved.")

        print("\n[3/3] Saving authentication state...")
        storage_path = Path(storage_state_path)
        await context.storage_state(path=str(storage_path))

        await context.close()
        await browser.close()

        if storage_path.exists():
            print(f"\n[success] Authentication state saved to: {storage_state_path}")
            print(f"  File size: {storage_path.stat().st_size} bytes")
            print("\n[info] Setup complete! You can now run the scraper with:")
            print("  python -m axiom.cli.run_scrape --mode=pulse")
        else:
            print("\n[error] Failed to save authentication state", file=sys.stderr)
            sys.exit(1)


async def verify_authentication(
    storage_state_path: str = "storage_state.json",
    url: str = "https://axiom.trade/pulse?chain=sol",
) -> bool:
    """
    Verify that the saved authentication still works.

    Args:
        storage_state_path: Path to the Playwright storage state file.
        url: Page to load for verification; defaults to Pulse dashboard.

    Returns:
        True if authentication is valid, False otherwise.
    """
    storage_path = Path(storage_state_path)

    if not storage_path.exists():
        print(f"[error] Storage state file not found: {storage_state_path}")
        return False

    print(f"Verifying authentication from: {storage_state_path}")

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=str(storage_path))
        page = await context.new_page()

        try:
            print("Navigating to Axiom...")
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=10000)

            current_url = page.url
            print(f"Current URL: {current_url}")

            if "login" in current_url.lower() or "auth" in current_url.lower():
                print("[error] Authentication expired - redirected to login.")
                return False

            print("[success] Authentication is valid.")
            return True
        except Exception as error:
            print(f"[error] Error verifying authentication: {error}")
            return False
        finally:
            await context.close()
            await browser.close()


def main() -> None:
    """Entry point for the authentication helper CLI."""
    import argparse

    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    parser = argparse.ArgumentParser(description="Setup Axiom authentication")
    parser.add_argument(
        "--storage-state",
        type=str,
        default="storage_state.json",
        help="Path to save storage state file.",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify existing authentication instead of setting up new.",
    )

    args = parser.parse_args()

    try:
        if args.verify:
            is_valid = asyncio.run(
                verify_authentication(storage_state_path=args.storage_state)
            )
            sys.exit(0 if is_valid else 1)
        else:
            asyncio.run(
                setup_authentication(
                    storage_state_path=args.storage_state, browser_channel="chrome"
                )
            )
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(1)
    except Exception as error:
        print(f"\n[error] Setup failed: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
