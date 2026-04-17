"""Canadian company portal scanner — Greenhouse/Lever/Ashby APIs + Playwright fallback."""
from __future__ import annotations

import asyncio
import logging
import re
from html.parser import HTMLParser

import httpx

from app.core.canadian_portals import CANADIAN_PORTALS, PortalConfig

logger = logging.getLogger(__name__)

_UA = "Mozilla/5.0 (compatible; JobHuntBot/1.0)"
_HEADERS = {"User-Agent": _UA, "Accept": "application/json"}


# ── HTML strip helper ─────────────────────────────────────────────────────────

class _HTMLStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return " ".join(self._parts)


def _strip_html(html: str) -> str:
    p = _HTMLStripper()
    p.feed(html or "")
    return p.get_text()[:3000]


# ── Keyword filter helper ─────────────────────────────────────────────────────

def _matches_keywords(text: str, keywords: list[str]) -> bool:
    if not keywords:
        return True
    lower = text.lower()
    return any(k.lower() in lower for k in keywords)


# ── Normalised job dict ───────────────────────────────────────────────────────

def _normalise(
    title: str,
    url: str,
    location: str | None,
    description: str | None,
    company: str,
    board: str,
) -> dict:
    return {
        "title": title,
        "company": company,
        "location": location or "",
        "description": description or "",
        "board": board,
        "job_url": url,
        "is_remote": bool(location and "remote" in location.lower()),
        "skills": [],
        "match_score": None,
        "fit_analysis": None,
        "archetype": "",
    }


# ── ATS-specific scrapers ─────────────────────────────────────────────────────

async def _scan_greenhouse(
    client: httpx.AsyncClient,
    portal: PortalConfig,
    keywords: list[str],
    max_results: int,
) -> list[dict]:
    board_id = portal["greenhouse_id"]
    try:
        resp = await client.get(
            f"https://boards-api.greenhouse.io/v1/boards/{board_id}/jobs?content=true",
            headers=_HEADERS,
            timeout=10.0,
        )
        if resp.status_code != 200:
            return []
        jobs_data = resp.json().get("jobs", [])
        results = []
        for j in jobs_data:
            title = j.get("title", "")
            desc_html = j.get("content", "")
            desc = _strip_html(desc_html)
            if not _matches_keywords(title + " " + desc, keywords):
                continue
            results.append(_normalise(
                title=title,
                url=j.get("absolute_url", ""),
                location=j.get("location", {}).get("name"),
                description=desc,
                company=portal["name"],
                board=f"greenhouse:{portal['name']}",
            ))
            if len(results) >= max_results:
                break
        return results
    except Exception as exc:
        logger.warning("Greenhouse scan failed for %s: %s", portal["name"], exc)
        return []


async def _scan_lever(
    client: httpx.AsyncClient,
    portal: PortalConfig,
    keywords: list[str],
    max_results: int,
) -> list[dict]:
    company_id = portal["lever_id"]
    try:
        resp = await client.get(
            f"https://api.lever.co/v0/postings/{company_id}?mode=json",
            headers=_HEADERS,
            timeout=10.0,
        )
        if resp.status_code != 200:
            return []
        postings = resp.json()
        if not isinstance(postings, list):
            postings = postings.get("postings", [])
        results = []
        for j in postings:
            title = j.get("text", "")
            desc = j.get("descriptionPlain", "") or _strip_html(j.get("description", ""))
            if not _matches_keywords(title + " " + desc, keywords):
                continue
            categories = j.get("categories", {})
            location = categories.get("location", "") or categories.get("city", "")
            results.append(_normalise(
                title=title,
                url=j.get("hostedUrl", ""),
                location=location,
                description=desc[:3000],
                company=portal["name"],
                board=f"lever:{portal['name']}",
            ))
            if len(results) >= max_results:
                break
        return results
    except Exception as exc:
        logger.warning("Lever scan failed for %s: %s", portal["name"], exc)
        return []


async def _scan_ashby(
    client: httpx.AsyncClient,
    portal: PortalConfig,
    keywords: list[str],
    max_results: int,
) -> list[dict]:
    board_id = portal["ashby_id"]
    try:
        resp = await client.post(
            f"https://api.ashbyhq.com/posting-api/job-board/{board_id}",
            json={"jobBoardName": board_id},
            headers={**_HEADERS, "Content-Type": "application/json"},
            timeout=10.0,
        )
        if resp.status_code != 200:
            return []
        postings = resp.json().get("jobPostings", [])
        results = []
        for j in postings:
            title = j.get("title", "")
            desc = _strip_html(j.get("descriptionHtml", ""))
            if not _matches_keywords(title + " " + desc, keywords):
                continue
            location = j.get("locationName", "") or j.get("teamName", "")
            results.append(_normalise(
                title=title,
                url=j.get("jobUrl", ""),
                location=location,
                description=desc,
                company=portal["name"],
                board=f"ashby:{portal['name']}",
            ))
            if len(results) >= max_results:
                break
        return results
    except Exception as exc:
        logger.warning("Ashby scan failed for %s: %s", portal["name"], exc)
        return []


async def _scan_custom_playwright(
    portal: PortalConfig,
    keywords: list[str],
    max_results: int,
) -> list[dict]:
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_extra_http_headers({"User-Agent": _UA})
            try:
                await page.goto(portal["url"], timeout=15_000)
                await page.wait_for_load_state("networkidle", timeout=15_000)
            except Exception:
                await browser.close()
                return []

            # Generic job listing extraction
            job_elements = await page.query_selector_all(
                "a[href*='job'], a[href*='career'], a[href*='position'], "
                "a[href*='opening'], a[href*='apply']"
            )
            results = []
            seen_urls: set[str] = set()
            for el in job_elements[:max_results * 3]:
                try:
                    text = (await el.inner_text()).strip()
                    href = await el.get_attribute("href") or ""
                    if not text or len(text) < 3 or href in seen_urls:
                        continue
                    if not _matches_keywords(text, keywords):
                        continue
                    full_url = href if href.startswith("http") else portal["url"].rstrip("/") + "/" + href.lstrip("/")
                    seen_urls.add(href)
                    results.append(_normalise(
                        title=text[:200],
                        url=full_url,
                        location=portal["city"] + ", " + portal["province"],
                        description="",
                        company=portal["name"],
                        board=f"custom:{portal['name']}",
                    ))
                    if len(results) >= max_results:
                        break
                except Exception:
                    continue

            await browser.close()
            return results
    except Exception as exc:
        logger.warning("Playwright scan failed for %s: %s", portal["name"], exc)
        return []


# ── Main scanner ──────────────────────────────────────────────────────────────

async def scan_canadian_portals(
    keywords: list[str],
    provinces: list[str] | None = None,
    ats_types: list[str] | None = None,
    max_results_per_portal: int = 10,
) -> list[dict]:
    """
    Scans Canadian company portals for job listings matching keywords.
    Greenhouse/Lever/Ashby run concurrently via httpx.
    Custom ATS portals run sequentially via Playwright.
    """
    portals = list(CANADIAN_PORTALS)
    if provinces:
        prov_upper = [p.upper() for p in provinces]
        portals = [p for p in portals if p["province"].upper() in prov_upper]
    if ats_types:
        portals = [p for p in portals if p["ats"] in ats_types]

    api_portals = [p for p in portals if p["ats"] in ("greenhouse", "lever", "ashby")]
    custom_portals = [p for p in portals if p["ats"] == "custom"]

    all_results: list[dict] = []
    seen_urls: set[str] = set()

    # Concurrent API-based scans
    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks = []
        for portal in api_portals:
            if portal["ats"] == "greenhouse":
                tasks.append(_scan_greenhouse(client, portal, keywords, max_results_per_portal))
            elif portal["ats"] == "lever":
                tasks.append(_scan_lever(client, portal, keywords, max_results_per_portal))
            elif portal["ats"] == "ashby":
                tasks.append(_scan_ashby(client, portal, keywords, max_results_per_portal))

        if tasks:
            batch = await asyncio.gather(*tasks, return_exceptions=True)
            for res in batch:
                if isinstance(res, list):
                    for job in res:
                        url = job.get("job_url", "")
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            all_results.append(job)

    # Sequential Playwright scans for custom portals
    for portal in custom_portals:
        try:
            results = await _scan_custom_playwright(portal, keywords, max_results_per_portal)
            for job in results:
                url = job.get("job_url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_results.append(job)
        except Exception as exc:
            logger.warning("Custom portal scan failed for %s: %s", portal["name"], exc)
        await asyncio.sleep(1.0)

    all_results.sort(key=lambda j: j.get("company", ""))
    logger.info("Portal scan complete: %d jobs from %d portals", len(all_results), len(portals))
    return all_results
