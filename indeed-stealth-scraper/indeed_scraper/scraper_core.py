"""
scraper_core.py — Indeed Canada job scraping: navigation, data extraction, pagination.
"""

import asyncio
import json
import random
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote_plus

from playwright.async_api import Page, TimeoutError as PwTimeout

from .browser_manager import BrowserManager
from .logger import get_logger
from .proxy_manager import ProxyManager

log = get_logger(__name__)

BASE_URL = "https://ca.indeed.com/jobs"
MAX_RETRIES = 3
BACKOFF_BASE = 2.0  # seconds

# Session cookies file — created by `python tests/capture_session.py`
_SESSION_FILE = Path("session/indeed_cookies.json")


# ---------------------------------------------------------------------------
# Block detection
# ---------------------------------------------------------------------------


def _is_blocked(title: str, content: str) -> bool:
    """Return True if the page looks like a Cloudflare / captcha / auth block."""
    title_lower = title.lower()
    content_lower = content.lower()

    # Match on page title — these patterns are unique to block/auth pages
    title_signals = [
        "just a moment",           # Cloudflare JS challenge
        "security check",          # hCaptcha / bot-check interstitial
        "sign in | indeed",        # Indeed auth redirect (precise title match)
        "indeed accounts",         # Auth redirect sub-string
        "access denied",
        "403 forbidden",
    ]
    if any(sig in title_lower for sig in title_signals):
        return True

    # Match on page content — only signals that don't appear on normal job pages
    content_signals = [
        "enable javascript",
        "cf-browser-verification",
        "captcha",
        "are you a robot",
        "unusual traffic",
    ]
    return any(sig in content_lower for sig in content_signals)


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------


async def _load_session_cookies(page: Page) -> None:
    """
    Inject saved Indeed session cookies into the page context.
    Cookies are created by running:  python tests/capture_session.py
    No-op if the session file doesn't exist.
    """
    if not _SESSION_FILE.exists():
        return
    try:
        cookies = json.loads(_SESSION_FILE.read_text(encoding="utf-8"))
        await page.context.add_cookies(cookies)
        log.info(f"Session loaded: {len(cookies)} cookies from {_SESSION_FILE}")
    except Exception as exc:
        log.warning(f"Could not load session cookies: {exc}")


# ---------------------------------------------------------------------------
# Data extraction
# ---------------------------------------------------------------------------


async def _extract_jobs_from_page(page: Page) -> list[dict]:
    """
    Pull job data from the Indeed page by reading window.mosaic.providerData
    and the jobKeysWithInfo object injected by Indeed's React app.

    Returns a (possibly empty) list of raw job dicts.
    """
    raw_jobs: list[dict] = []

    try:
        jobs_data: Any = await page.evaluate(
            """
            () => {
                try {
                    const mosaic = window.mosaic || {};
                    const providerData = mosaic.providerData || {};

                    // Primary: mosaic-provider-jobcards (try jobCards then results)
                    const jobcards = providerData['mosaic-provider-jobcards'] || {};
                    const model = jobcards.metaData
                        ? jobcards.metaData.mosaicProviderJobCardsModel
                        : null;
                    if (model) {
                        const jobs = model.jobCards || model.results;
                        if (jobs && jobs.length) return jobs;
                    }

                    // Secondary: jobKeysWithInfo
                    const initialState = window._initialData || {};
                    const jobKeysWithInfo = initialState.jobKeysWithInfo || {};
                    if (Object.keys(jobKeysWithInfo).length > 0) {
                        return Object.values(jobKeysWithInfo);
                    }

                    // Tertiary: serialised JSON in a script tag
                    const scripts = document.querySelectorAll('script[type="text/javascript"]');
                    for (const s of scripts) {
                        const text = s.textContent || '';
                        const match = text.match(/window\\.mosaic\\.providerData\\["mosaic-provider-jobcards"\\]\\s*=\\s*(\\{.*?\\});/s);
                        if (match) {
                            try {
                                const parsed = JSON.parse(match[1]);
                                const m = parsed?.metaData?.mosaicProviderJobCardsModel;
                                const nested = m && (m.jobCards || m.results);
                                if (nested && nested.length) return nested;
                            } catch (_) {}
                        }
                    }
                } catch (e) {
                    return [];
                }
                return [];
            }
            """
        )
        if isinstance(jobs_data, list):
            raw_jobs = jobs_data
    except Exception as exc:
        log.warning(f"JS extraction failed: {exc}")

    if not raw_jobs:
        # Fallback: parse job cards from visible DOM attributes
        raw_jobs = await _dom_fallback(page)

    log.debug(f"Extracted {len(raw_jobs)} raw jobs from page.")
    return raw_jobs


async def _dom_fallback(page: Page) -> list[dict]:
    """
    Minimal DOM scrape when JS data objects are unavailable.
    Reads data attributes on job card elements.
    """
    try:
        jobs: Any = await page.evaluate(
            """
            () => {
                const cards = document.querySelectorAll('[data-jk]');
                return Array.from(cards).map(card => ({
                    jobkey: card.getAttribute('data-jk'),
                    title: (card.querySelector('.jobTitle, [class*="jobTitle"]') || {}).innerText,
                    company: (card.querySelector('[data-testid="company-name"], .companyName') || {}).innerText,
                    formattedLocation: (card.querySelector('[data-testid="text-location"], .companyLocation') || {}).innerText,
                    snippet: (card.querySelector('.job-snippet, [class*="snippet"]') || {}).innerText,
                    formattedRelativeTime: (card.querySelector('[class*="date"]') || {}).innerText,
                }));
            }
            """
        )
        return [j for j in (jobs or []) if j.get("jobkey")]
    except Exception as exc:
        log.debug(f"DOM fallback failed: {exc}")
        return []


# ---------------------------------------------------------------------------
# Core scraper
# ---------------------------------------------------------------------------


class IndeedScraper:
    """
    Orchestrates browser sessions, page navigation, and data extraction
    for Indeed Canada job listings.
    """

    def __init__(
        self,
        proxy_manager: Optional[ProxyManager] = None,
        max_pages: int = 10,
    ) -> None:
        self._proxy_mgr = proxy_manager
        self._max_pages = max_pages

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def scrape(self, query: str, location: str) -> list[dict]:
        """
        Scrape up to max_pages of results for the given query and location.
        Returns a flat list of raw job dicts.
        """
        all_jobs: list[dict] = []
        proxy: Optional[str] = None

        for page_num in range(self._max_pages):
            start = page_num * 10  # Indeed uses ?start=N (10 results per page)
            url = self._build_url(query, location, start)

            log.info(f"Scraping page {page_num + 1}/{self._max_pages} | start={start}")

            if self._proxy_mgr and self._proxy_mgr.has_proxies():
                proxy = self._proxy_mgr.get_next()

            jobs = await self._scrape_page_with_retry(url, proxy=proxy)
            if jobs is None:
                log.warning(f"Page {page_num + 1} exhausted retries — stopping pagination.")
                break
            if not jobs:
                log.info("No jobs on this page — end of results.")
                break

            all_jobs.extend(jobs)
            log.info(f"Page {page_num + 1}: +{len(jobs)} jobs | running total: {len(all_jobs)}")

            # Polite delay between pages
            await BrowserManager.human_delay(1.0, 3.0)

        return all_jobs

    # ------------------------------------------------------------------
    # Per-page retry logic
    # ------------------------------------------------------------------

    async def _scrape_page_with_retry(
        self,
        url: str,
        proxy: Optional[str] = None,
    ) -> Optional[list[dict]]:
        """
        Try to scrape a single URL up to MAX_RETRIES times.
        Returns the list of jobs, an empty list (no results), or None (fatal failure).
        """
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                jobs = await self._fetch_page(url, proxy=proxy)
                return jobs
            except BlockedError as exc:
                log.warning(f"Attempt {attempt}/{MAX_RETRIES} — blocked: {exc}")
                if self._proxy_mgr and proxy:
                    self._proxy_mgr.mark_failed(proxy)
                    proxy = self._proxy_mgr.get_next()
                backoff = BACKOFF_BASE ** attempt + random.uniform(0, 1)
                log.info(f"Backing off {backoff:.1f}s before retry …")
                await asyncio.sleep(backoff)
            except Exception as exc:
                log.error(f"Attempt {attempt}/{MAX_RETRIES} — unexpected error: {exc}")
                backoff = BACKOFF_BASE ** attempt
                await asyncio.sleep(backoff)

        return None  # All retries exhausted

    # ------------------------------------------------------------------
    # Single page fetch
    # ------------------------------------------------------------------

    async def _fetch_page(
        self,
        url: str,
        proxy: Optional[str] = None,
    ) -> list[dict]:
        """
        Open a browser, navigate to url, extract jobs, and return them.
        Raises BlockedError if Cloudflare / anti-bot is detected.
        """
        async with BrowserManager(proxy=proxy) as bm:
            page = await bm.new_page()
            await _load_session_cookies(page)

            log.info(f"Navigating -> {url}")

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            except PwTimeout:
                log.warning(f"Navigation timeout for {url}")
                raise

            # Wait for Indeed's React app to hydrate and populate mosaic data.
            # This is the critical step — without it the JS extraction always
            # falls back to the DOM (which caps at ~15 visible cards).
            try:
                await page.wait_for_function(
                    """() => {
                        try {
                            const pd = window.mosaic && window.mosaic.providerData;
                            if (!pd) return false;
                            const jc = pd['mosaic-provider-jobcards'];
                            return !!(jc && jc.metaData &&
                                      jc.metaData.mosaicProviderJobCardsModel);
                        } catch (e) { return false; }
                    }""",
                    timeout=10_000,
                )
                log.debug("Mosaic provider data ready.")
            except Exception:
                # Best-effort: data may still be partially available
                log.debug("Mosaic wait timed out — extracting whatever is available.")
                await bm.human_delay(1.0, 2.0)

            title = await page.title()
            content_snippet = (await page.content())[:2000]

            if _is_blocked(title, content_snippet):
                raise BlockedError(f"Block detected | title='{title}'")

            await bm.subtle_mouse_move(page)

            jobs = await _extract_jobs_from_page(page)
            log.info(f"Extracted {len(jobs)} raw jobs | url={url}")
            return jobs

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_url(query: str, location: str, start: int = 0) -> str:
        q = quote_plus(query)
        l = quote_plus(location)
        # Always include &start= and &l= on every URL — never rely on cookies/session
        return f"{BASE_URL}?q={q}&l={l}&start={start}"


    # ------------------------------------------------------------------
    # Description enrichment
    # ------------------------------------------------------------------

    async def enrich_with_descriptions(self, jobs: list[dict]) -> list[dict]:
        """
        For each job that lacks a full description, visit its detail page and
        extract the full text from #jobDescriptionText.  Falls back to snippet
        on any error.  Mutates and returns the same list.
        """
        to_fetch = []
        for job in jobs:
            existing = job.get("description") or job.get("snippet") or ""
            job_id = job.get("jobkey") or job.get("jobKey") or job.get("job_id")
            if job_id and len(existing) < 400:
                to_fetch.append((job, job_id))

        if not to_fetch:
            return jobs

        log.info(f"Enriching descriptions for {len(to_fetch)}/{len(jobs)} jobs …")

        async with BrowserManager() as bm:
            page = await bm.new_page()
            await _load_session_cookies(page)

            for job, job_id in to_fetch:
                url = f"https://ca.indeed.com/viewjob?jk={job_id}"
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=20_000)
                    desc: Optional[str] = await page.evaluate(
                        """() => {
                            const el = document.querySelector('#jobDescriptionText');
                            if (el) return el.innerText;
                            try {
                                const d = window._initialData
                                    ?.jobInfoWrapperModel
                                    ?.jobInfoModel
                                    ?.sanitizedHtmlJobDescription;
                                if (d) {
                                    const t = document.createElement('div');
                                    t.innerHTML = d;
                                    return t.innerText;
                                }
                            } catch (_) {}
                            return null;
                        }"""
                    )
                    if desc and len(desc) > 100:
                        job["description"] = desc
                        log.debug(f"  {job_id}: {len(desc)} chars")
                except Exception as exc:
                    log.debug(f"  {job_id}: description fetch failed — {exc}")

                await BrowserManager.human_delay(0.4, 1.2)

        return jobs


class BlockedError(Exception):
    """Raised when Indeed returns a bot-detection / Cloudflare challenge page."""
