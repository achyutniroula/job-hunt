"""
Scraper for Eluta.ca — Canada's largest job search engine aggregating
postings from employer websites directly.
"""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, RawJob
from app.scrapers.jobspy_scraper import _extract_skills, _infer_seniority

logger = logging.getLogger(__name__)

ELUTA_BASE = "https://www.eluta.ca"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-CA,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class ElutaScraper(BaseScraper):
    board_name = "eluta"

    async def scrape(
        self,
        keywords: str,
        location: str,
        remote_only: bool = False,
        max_results: int = 25,
    ) -> list[RawJob]:
        results: list[RawJob] = []
        page = 1

        async with httpx.AsyncClient(
            headers=HEADERS, follow_redirects=True, timeout=15.0
        ) as client:
            while len(results) < max_results:
                url = self._build_url(keywords, location, remote_only, page)
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                except Exception as exc:
                    logger.warning("Eluta request failed (page %d): %s", page, exc)
                    break

                page_jobs = self._parse_page(resp.text)
                if not page_jobs:
                    break

                results.extend(page_jobs)
                page += 1
                await asyncio.sleep(1.5)  # polite rate limit

        return results[:max_results]

    # ── helpers ──────────────────────────────────────────────────────────────

    def _build_url(
        self, keywords: str, location: str, remote_only: bool, page: int
    ) -> str:
        q = quote_plus(keywords)
        loc = quote_plus(location) if not remote_only else quote_plus("Remote")
        offset = (page - 1) * 20
        return f"{ELUTA_BASE}/search?q={q}&l={loc}&start={offset}"

    def _parse_page(self, html: str) -> list[RawJob]:
        soup = BeautifulSoup(html, "lxml")
        jobs: list[RawJob] = []

        # Eluta job cards use article.result or div.result
        cards = soup.select("div.result") or soup.select("article.result")
        for card in cards:
            try:
                jobs.append(self._parse_card(card))
            except Exception as e:
                logger.debug("Eluta card parse error: %s", e)

        return jobs

    def _parse_card(self, card) -> RawJob:
        title_el = card.select_one("h2.title a") or card.select_one(".title a")
        title = title_el.get_text(strip=True) if title_el else "Unknown"
        job_url = ELUTA_BASE + title_el["href"] if title_el and title_el.get("href") else None

        company_el = card.select_one(".company") or card.select_one(".employer")
        company = company_el.get_text(strip=True) if company_el else None

        location_el = card.select_one(".location") or card.select_one(".city")
        location = location_el.get_text(strip=True) if location_el else None

        desc_el = card.select_one(".description") or card.select_one(".summary")
        description = desc_el.get_text(" ", strip=True) if desc_el else None

        date_el = card.select_one(".date") or card.select_one("time")
        posted_at = _parse_relative_date(date_el.get_text(strip=True) if date_el else "")

        return RawJob(
            title=title,
            board="eluta",
            company=company,
            location=location,
            description=description,
            skills=_extract_skills(description),
            seniority_level=_infer_seniority(title),
            is_remote="remote" in (location or "").lower(),
            job_url=job_url,
            posted_at=posted_at,
        )


def _parse_relative_date(text: str) -> datetime | None:
    """Convert 'X days ago' strings to approximate datetime."""
    text = text.lower().strip()
    try:
        import re as _re
        from datetime import timedelta

        m = _re.search(r"(\d+)\s+day", text)
        if m:
            return datetime.now(tz=timezone.utc) - timedelta(days=int(m.group(1)))
        if "today" in text or "just now" in text:
            return datetime.now(tz=timezone.utc)
        if "yesterday" in text:
            return datetime.now(tz=timezone.utc) - timedelta(days=1)
    except Exception:
        pass
    return None
