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
    persistent: bool = False,
    user_data_dir: str = ".user-data/axiom",
    no_prompt: bool = False,
) -> None:
    """
    Launch a browser for manual Google OAuth login and save the session state.

    Args:
        url: Axiom URL to open for authentication.
        storage_state_path: Destination file for the Playwright storage state.
        browser_channel: The Playwright browser channel (e.g., "chrome", "msedge").
        persistent: Launch a persistent context with a real user profile directory.
        user_data_dir: Directory for persistent user data when persistent=True.
        no_prompt: If True, do not block on interactive prompts.
    """
    print("=" * 60)
    print("Axiom Authentication Setup")
    print("=" * 60)
    print("\nThis will open a browser window where you can log in to Axiom.")
    print("After logging in successfully, return to this terminal.")
    print("\nYour session will be saved to:", storage_state_path)
    if not no_prompt:
        input("\nPress Enter to continue or Ctrl+C to cancel...")

    async with async_playwright() as playwright:
        print("\n[1/3] Launching browser...")
        common_args = ["--disable-blink-features=AutomationControlled"]
        context = None
        browser = None

        # Prefer a real installed browser channel to reduce OAuth friction
        channels_to_try = []
        if browser_channel:
            channels_to_try.append(browser_channel)
        # On Windows, Edge is commonly available
        if browser_channel != "msedge":
            channels_to_try.append("msedge")
        # Fallback to bundled Chromium (no channel)
        channels_to_try.append(None)

        last_error: Optional[Exception] = None

        for ch in channels_to_try:
            try:
                if persistent:
                    context = await playwright.chromium.launch_persistent_context(
                        user_data_dir=user_data_dir,
                        channel=ch,
                        headless=False,
                        args=common_args,
                        viewport={"width": 1920, "height": 1080},
                        accept_downloads=True,
                    )
                    browser = context.browser
                else:
                    launch_kwargs: dict[str, Any] = {"headless": False, "args": common_args}
                    if ch:
                        launch_kwargs["channel"] = ch
                    browser = await playwright.chromium.launch(**launch_kwargs)
                    context = await browser.new_context(
                        viewport={"width": 1920, "height": 1080}
                    )

                # If we made it here without exception, we are launched
                if ch:
                    print(f"[info] Using browser channel: {ch} (persistent={persistent})")
                else:
                    print(
                        f"[warning] Using bundled Chromium (channel unavailable). persistent={persistent}"
                    )
                last_error = None
                break
            except Exception as e:
                last_error = e
                if ch:
                    print(f"[warning] Failed to launch channel '{ch}': {e}")
                else:
                    print(f"[warning] Failed to launch bundled Chromium: {e}")
                continue

        if context is None:
            # Exhausted all options
            raise RuntimeError(
                f"Could not launch any browser (last_error={last_error})"
            )

        print("[2/3] Opening Axiom login page...")
        page = await context.new_page()
        # Minimal stealth to reduce automation fingerprint for Google OAuth
        await page.add_init_script(
            """
            // Hide webdriver flag
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            // Set languages
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            // Fake plugins length
            Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
            """
        )

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
            if not no_prompt:
                input(
                    "\nPress Enter here once you are logged in and see the dashboard..."
                )
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

    # On Windows, Playwright spawns subprocesses; using the Selector policy
    # breaks asyncio.create_subprocess_exec with NotImplementedError.
    # Ensure the Proactor policy (default on Python 3.8+) is used.
    if sys.platform.startswith("win") and hasattr(asyncio, "WindowsProactorEventLoopPolicy"):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

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
    parser.add_argument(
        "--browser-channel",
        type=str,
        default="chrome",
        help="Browser channel to use (e.g., 'chrome', 'msedge').",
    )
    parser.add_argument(
        "--persistent",
        action="store_true",
        help="Use persistent user profile to reduce OAuth friction.",
    )
    parser.add_argument(
        "--user-data-dir",
        type=str,
        default=".user-data/axiom",
        help="Directory for persistent browser profile (when --persistent).",
    )
    parser.add_argument(
        "--no-prompt",
        action="store_true",
        help="Skip interactive prompts (advanced).",
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
                    storage_state_path=args.storage_state,
                    browser_channel=args.browser_channel,
                    persistent=bool(args.persistent),
                    user_data_dir=args.user_data_dir,
                    no_prompt=bool(args.no_prompt),
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
