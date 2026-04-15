"""
tests/capture_session.py — One-time tool to save an Indeed login session.

Run this script ONCE to open a headed browser, log into Indeed, then save the
session cookies so the scraper can reuse them for paginated requests.

Usage:
    python tests/capture_session.py

The saved cookies are written to:  session/indeed_cookies.json

After that, run the scraper normally — it will automatically load the session.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# Force headed mode — this script always needs a visible browser for login.
os.environ["DEBUG"] = "1"

SESSION_DIR = ROOT / "session"
SESSION_FILE = SESSION_DIR / "indeed_cookies.json"

LOGIN_URL = "https://ca.indeed.com/account/login"
VERIFY_URL = "https://ca.indeed.com/jobs?q=software+developer&l=Ontario"


async def main() -> None:
    from indeed_scraper.browser_manager import BrowserManager

    print("\nOpening browser -- log into Indeed, then come back here.", flush=True)
    print(f"Navigating to: {LOGIN_URL}\n", flush=True)

    async with BrowserManager() as bm:
        page = await bm.new_page()
        await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30_000)

        print("Browser is open. Log in to your Indeed account.", flush=True)
        print("Press ENTER here once you are logged in and on the main Indeed page.")
        input()

        # Navigate to a search page to pick up any search-session cookies.
        # Ignore navigation interruptions — cookies are captured regardless.
        print("Navigating to a job search page to capture all cookies...", flush=True)
        try:
            await page.goto(VERIFY_URL, wait_until="domcontentloaded", timeout=30_000)
        except Exception:
            pass  # page may redirect; cookies are still set
        await asyncio.sleep(3)

        title = await page.title()
        print(f"Page title: {title!r}", flush=True)

        cookies = await page.context.cookies()
        SESSION_DIR.mkdir(exist_ok=True)
        SESSION_FILE.write_text(json.dumps(cookies, indent=2), encoding="utf-8")

        print(f"\nSaved {len(cookies)} cookies to {SESSION_FILE}", flush=True)
        print("The scraper will now use this session for paginated requests.", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
