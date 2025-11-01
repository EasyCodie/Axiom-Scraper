"""
Authentication setup script for Axiom.

This script opens a browser where you can log in to Axiom with Google OAuth.
Your session will be saved to storage_state.json for reuse by the scraper.

Usage:
    python scripts/setup_auth.py
"""

import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright


async def setup_authentication(
    url: str = "https://axiom.trade",
    storage_state_path: str = "storage_state.json"
) -> None:
    """
    Launch a browser for manual Google OAuth login and save the session.
    
    Args:
        url: Axiom login URL
        storage_state_path: Path to save the authenticated session state
    """
    print("=" * 60)
    print("Axiom Authentication Setup")
    print("=" * 60)
    print("\nThis will open a browser window where you can log in to Axiom.")
    print("After logging in successfully, close the browser window.")
    print("\nYour session will be saved to:", storage_state_path)
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    input()
    
    async with async_playwright() as p:
        print("\n[1/3] Launching browser...")
        browser = await p.chromium.launch(headless=False)
        
        # Create a new context (no storage state yet)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        
        print("[2/3] Opening Axiom login page...")
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            print("\n" + "=" * 60)
            print("PLEASE LOG IN TO AXIOM IN THE BROWSER WINDOW")
            print("=" * 60)
            print("\nInstructions:")
            print("1. Click the Google login button")
            print("2. Complete the Google OAuth flow")
            print("3. Wait until you see the Axiom dashboard")
            print("4. Close the browser window")
            print("\nWaiting for you to log in...")
            
            # Wait for user to close the browser
            await page.wait_for_event("close", timeout=300000)  # 5 minutes
            
        except Exception as e:
            print(f"\n⚠ Timeout or error: {e}")
            print("If you've logged in successfully, the session may still be saved.")
        
        print("\n[3/3] Saving authentication state...")
        
        # Save the storage state (cookies, local storage, etc.)
        storage_path = Path(storage_state_path)
        await context.storage_state(path=str(storage_path))
        
        await context.close()
        await browser.close()
        
        if storage_path.exists():
            print(f"\n✓ Authentication state saved to: {storage_state_path}")
            print(f"  File size: {storage_path.stat().st_size} bytes")
            print("\n✓ Setup complete! You can now run the scraper with:")
            print("  python -m axiom.cli.run_scrape --mode=pulse")
        else:
            print(f"\n✗ Failed to save authentication state", file=sys.stderr)
            sys.exit(1)


async def verify_authentication(storage_state_path: str = "storage_state.json") -> bool:
    """
    Verify that the saved authentication still works.
    
    Args:
        storage_state_path: Path to the storage state file
        
    Returns:
        True if authentication is valid, False otherwise
    """
    storage_path = Path(storage_state_path)
    
    if not storage_path.exists():
        print(f"✗ Storage state file not found: {storage_state_path}")
        return False
    
    print(f"Verifying authentication from: {storage_state_path}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # Load the saved storage state
        context = await browser.new_context(storage_state=str(storage_path))
        page = await context.new_page()
        
        try:
            print("Navigating to Axiom...")
            await page.goto("https://axiom.trade/pulse?chain=sol", timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=10000)
            
            # Check if we're on the pulse page (not redirected to login)
            url = page.url
            print(f"Current URL: {url}")
            
            if "login" in url.lower() or "auth" in url.lower():
                print("✗ Authentication expired - redirected to login")
                return False
            
            print("✓ Authentication is valid")
            return True
            
        except Exception as e:
            print(f"✗ Error verifying authentication: {e}")
            return False
        finally:
            await context.close()
            await browser.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup Axiom authentication")
    parser.add_argument(
        "--storage-state",
        type=str,
        default="storage_state.json",
        help="Path to save storage state file"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify existing authentication instead of setting up new"
    )
    
    args = parser.parse_args()
    
    try:
        if args.verify:
            is_valid = asyncio.run(verify_authentication(args.storage_state))
            sys.exit(0 if is_valid else 1)
        else:
            asyncio.run(setup_authentication(storage_state_path=args.storage_state))
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Setup failed: {e}", file=sys.stderr)
        sys.exit(1)
