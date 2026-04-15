"""
browser_manager.py — Stealth Playwright browser lifecycle management.
"""

import asyncio
import os
import random
from typing import Optional

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

from .logger import get_logger

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Stealth configuration helpers
# ---------------------------------------------------------------------------

_USER_AGENTS: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

_VIEWPORTS: list[dict] = [
    {"width": 1366, "height": 768},
    {"width": 1440, "height": 900},
    {"width": 1920, "height": 1080},
    {"width": 1280, "height": 800},
    {"width": 1536, "height": 864},
]

_LOCALES: list[str] = ["en-CA", "en-US", "en-GB"]

# JavaScript injected into every page to mask automation signals
_STEALTH_SCRIPT = """
() => {
    // Remove webdriver property
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

    // Mock plugins list (non-zero length)
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5],
    });

    // Mock languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-CA', 'en-US', 'en'],
    });

    // Prevent chrome automation check
    window.chrome = { runtime: {} };

    // Permissions mock (avoid automation detection via query)
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) =>
        parameters.name === 'notifications'
            ? Promise.resolve({ state: Notification.permission })
            : originalQuery(parameters);
}
"""


class BrowserManager:
    """
    Manages a single Playwright Chromium browser instance with stealth settings.

    Usage:
        async with BrowserManager(proxy="http://host:port") as bm:
            page = await bm.new_page()
            ...
    """

    def __init__(
        self,
        proxy: Optional[str] = None,
        browser_type: str = "chromium",
    ) -> None:
        self._proxy = proxy
        self._browser_type = browser_type
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

    # ------------------------------------------------------------------
    # Async context manager
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "BrowserManager":
        await self._launch()
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()

    # ------------------------------------------------------------------
    # Launch / close
    # ------------------------------------------------------------------

    async def _launch(self) -> None:
        headless = os.environ.get("DEBUG", "0") != "1"
        log.info(
            f"Launching {self._browser_type} | headless={headless} | proxy={self._proxy}"
        )

        self._playwright = await async_playwright().start()
        browser_launcher = getattr(self._playwright, self._browser_type)

        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-infobars",
            "--disable-extensions",
        ]

        proxy_settings = None
        if self._proxy:
            proxy_url = self._proxy if "://" in self._proxy else f"http://{self._proxy}"
            proxy_settings = {"server": proxy_url}

        self._browser = await browser_launcher.launch(
            headless=headless,
            args=launch_args,
            proxy=proxy_settings,
        )

        ua = random.choice(_USER_AGENTS)
        viewport = random.choice(_VIEWPORTS)
        locale = random.choice(_LOCALES)

        self._context = await self._browser.new_context(
            user_agent=ua,
            viewport=viewport,
            locale=locale,
            java_script_enabled=True,
            # Accept cookies / storage to appear more like a real browser
            accept_downloads=False,
            bypass_csp=False,
        )

        # Inject stealth script before any page script runs
        await self._context.add_init_script(script=_STEALTH_SCRIPT)

        log.debug(f"Browser context created | UA={ua[:50]}… | viewport={viewport}")

    async def close(self) -> None:
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        log.debug("Browser closed.")

    # ------------------------------------------------------------------
    # Page factory
    # ------------------------------------------------------------------

    async def new_page(self) -> Page:
        """Open and return a new stealth page."""
        assert self._context is not None, "BrowserManager not started — use async with."
        page = await self._context.new_page()
        return page

    # ------------------------------------------------------------------
    # Human-like interaction helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def human_delay(min_s: float = 0.5, max_s: float = 2.5) -> None:
        """Sleep for a random duration to mimic human pacing."""
        delay = random.uniform(min_s, max_s)
        await asyncio.sleep(delay)

    @staticmethod
    async def subtle_mouse_move(page: Page) -> None:
        """
        Move the mouse along a short random path before an interaction
        to reduce automation signal from perfectly still cursor.
        """
        start_x = random.randint(100, 800)
        start_y = random.randint(100, 500)
        end_x = start_x + random.randint(-50, 50)
        end_y = start_y + random.randint(-50, 50)
        await page.mouse.move(start_x, start_y)
        await asyncio.sleep(random.uniform(0.05, 0.15))
        await page.mouse.move(end_x, end_y)
        await asyncio.sleep(random.uniform(0.05, 0.2))
