"""
Scraper for JobBank.gc.ca — the Government of Canada's official job board.
Uses the public search endpoint which returns structured HTML.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, RawJob
from app.scrapers.jobspy_scraper import _extract_skills, _infer_seniority

logger = logging.getLogger(__name__)

JOBBANK_BASE = "https://www.jobbank.gc.ca"
SEARCH_URL = f"{JOBBANK_BASE}/jobsearch/jobsearch"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-CA,en;q=0.9",
    "Referer": JOBBANK_BASE,
}


class JobBankScraper(BaseScraper):
    board_name = "jobbank"

    async def scrape(
        self,
        keywords: str,
        location: str,
        remote_only: bool = False,
        max_results: int = 25,
        distance_km: int = 100,
    ) -> list[RawJob]:
        results: list[RawJob] = []
        page = 1
        page_size = 25

        async with httpx.AsyncClient(
            headers=HEADERS, follow_redirects=True, timeout=20.0
        ) as client:
            while len(results) < max_results:
                params = self._build_params(keywords, location, remote_only, page, page_size)
                try:
                    resp = await client.get(SEARCH_URL, params=params)
                    resp.raise_for_status()
                except Exception as exc:
                    logger.warning("JobBank request failed (page %d): %s", page, exc)
                    break

                page_jobs = self._parse_page(resp.text)
                if not page_jobs:
                    break

                results.extend(page_jobs)
                if len(page_jobs) < page_size:
                    break  # no more pages
                page += 1
                await asyncio.sleep(1.5)

        return results[:max_results]

    # ── helpers ──────────────────────────────────────────────────────────────

    def _build_params(
        self,
        keywords: str,
        location: str,
        remote_only: bool,
        page: int,
        page_size: int,
    ) -> dict:
        params: dict = {
            "searchstring": keywords,
            "locationstring": "" if remote_only else location,
            "sort": "D",        # Most recent first
            "action": "search",
            "button.submit": "Search",
            "pageSize": str(page_size),
            "currentPage": str(page),
        }
        if remote_only:
            params["remotework"] = "1"
        return params

    def _parse_page(self, html: str) -> list[RawJob]:
        soup = BeautifulSoup(html, "lxml")
        jobs: list[RawJob] = []

        # JobBank: article.action-buttons wraps each card; link inside has class resultJobItem
        cards = soup.select("article.action-buttons")
        for card in cards:
            try:
                jobs.append(self._parse_card(card))
            except Exception as e:
                logger.debug("JobBank card parse error: %s", e)

        return jobs

    def _parse_card(self, card) -> RawJob:
        # Title + URL — link is a.resultJobItem, title text in span.noctitle
        link_el = card.select_one("a.resultJobItem")
        job_url = None
        if link_el:
            href = link_el.get("href", "")
            # Strip jsessionid to get a clean URL
            href = href.split(";")[0]
            job_url = href if href.startswith("http") else JOBBANK_BASE + href

        title_el = card.select_one("span.noctitle")
        title = title_el.get_text(strip=True).title() if title_el else "Unknown"

        # Company
        business_el = card.select_one("li.business")
        company = business_el.get_text(strip=True) if business_el else None

        # Location — strip icon spans, keep plain text
        location_el = card.select_one("li.location")
        location = None
        if location_el:
            # Remove wb-inv spans (screen-reader text / icons)
            for s in location_el.select("span.wb-inv, i, span[aria-hidden]"):
                s.decompose()
            location = location_el.get_text(" ", strip=True) or None

        # Salary
        salary_el = card.select_one("li.salary")
        salary_text = salary_el.get_text(strip=True) if salary_el else ""
        salary_min, salary_max, salary_interval = _parse_salary_text(salary_text)

        # Date — strip icon spans first
        date_el = card.select_one("li.date")
        date_text = ""
        if date_el:
            for s in date_el.select("span.wb-inv, i, span[aria-hidden]"):
                s.decompose()
            date_text = date_el.get_text(" ", strip=True)
        posted_at = _parse_jobbank_date(date_text)

        # Description snippet
        desc_el = card.select_one("div.description") or card.select_one("p")
        description = desc_el.get_text(" ", strip=True) if desc_el else None

        return RawJob(
            title=title,
            board="jobbank",
            company=company,
            location=location,
            description=description,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency="CAD",
            salary_interval=salary_interval,
            skills=_extract_skills(description),
            seniority_level=_infer_seniority(title),
            is_remote="remote" in (location or "").lower(),
            job_url=job_url,
            posted_at=posted_at,
        )


def _parse_salary_text(
    text: str,
) -> tuple[float | None, float | None, str | None]:
    import re

    text = text.replace(",", "")
    numbers = re.findall(r"\$?([\d.]+)", text)
    lo = float(numbers[0]) if numbers else None
    hi = float(numbers[1]) if len(numbers) > 1 else lo

    interval = None
    tl = text.lower()
    if "hour" in tl:
        interval = "hourly"
    elif "week" in tl:
        interval = "weekly"
    elif "month" in tl:
        interval = "monthly"
    elif "year" in tl or "annual" in tl:
        interval = "yearly"

    return lo, hi, interval


def _parse_jobbank_date(text: str) -> datetime | None:
    text = text.lower().strip()
    now = datetime.now(tz=timezone.utc)
    try:
        import re as _re

        m = _re.search(r"(\d+)\s+day", text)
        if m:
            return now - timedelta(days=int(m.group(1)))
        if "today" in text:
            return now
        if "yesterday" in text:
            return now - timedelta(days=1)

        # Try parsing "Month DD, YYYY"
        from datetime import datetime as _dt
        for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d"):
            try:
                return _dt.strptime(text, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    except Exception:
        pass
    return None
