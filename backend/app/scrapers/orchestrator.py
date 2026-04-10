"""
Concurrent scraping orchestrator — incremental DB writes.

Each board scrapes concurrently; results are committed to DB immediately
when a board finishes (not batched at the end). The frontend can poll
GET /api/jobs/{session_id} during "running" status to show partial results.
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.models.job import Job
from app.models.session import ScrapeSession
from app.scrapers.base import BaseScraper, RawJob
from app.scrapers.eluta_scraper import ElutaScraper
from app.scrapers.jobbank_scraper import JobBankScraper
from app.scrapers.jobspy_scraper import (
    GlassdoorScraper,
    GoogleJobsScraper,
    IndeedScraper,
    LinkedInScraper,
    ZipRecruiterScraper,
)

logger = logging.getLogger(__name__)
settings = get_settings()

ALL_SCRAPERS: dict[str, type[BaseScraper]] = {
    "linkedin":     LinkedInScraper,
    "indeed":       IndeedScraper,
    "glassdoor":    GlassdoorScraper,
    "ziprecruiter": ZipRecruiterScraper,
    "google":       GoogleJobsScraper,
    "eluta":        ElutaScraper,
    "jobbank":      JobBankScraper,
}


async def run_scrape_session(
    session_id: str,
    keywords: str,
    location: str,
    remote_only: bool = False,
    boards: list[str] | None = None,
) -> int:
    """
    Run all scrapers concurrently. Each board's results are written to DB
    immediately on completion so the frontend can show partial results.
    Returns total jobs saved.
    """
    enabled_boards = boards or list(ALL_SCRAPERS.keys())
    max_per_board = settings.scraper_max_results_per_board
    scrape_semaphore = asyncio.Semaphore(settings.scraper_max_workers)
    # SQLite requires serialised writes
    db_lock = asyncio.Lock()
    # Shared dedup state (title|company)
    seen: set[str] = set()
    total_saved = 0

    # Mark session as running
    async with AsyncSessionLocal() as db:
        session_obj = await db.get(ScrapeSession, session_id)
        if session_obj:
            session_obj.status = "running"
            await db.commit()

    async def _scrape_board(board_name: str) -> list[RawJob]:
        factory = ALL_SCRAPERS.get(board_name)
        if not factory:
            return []
        scraper = factory()
        async with scrape_semaphore:
            logger.info("[%s] scraping '%s' in '%s'", board_name, keywords, location)
            try:
                jobs = await asyncio.wait_for(
                    scraper.scrape(keywords, location, remote_only, max_per_board),
                    timeout=60.0,
                )
                logger.info("[%s] returned %d jobs", board_name, len(jobs))
                return jobs
            except asyncio.TimeoutError:
                logger.warning("[%s] timed out", board_name)
                return []
            except Exception as exc:
                logger.error("[%s] error: %s", board_name, exc)
                return []

    async def _scrape_and_save(board_name: str) -> int:
        """Scrape one board then immediately persist results."""
        nonlocal total_saved
        raw_jobs = await _scrape_board(board_name)
        if not raw_jobs:
            return 0

        async with db_lock:
            new_jobs: list[Job] = []
            for raw in raw_jobs:
                key = f"{str(raw.title or '').lower()}|{str(raw.company or '').lower()}"
                if key in seen:
                    continue
                seen.add(key)
                new_jobs.append(Job(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    title=raw.title,
                    company=raw.company,
                    location=raw.location,
                    salary_min=raw.salary_min,
                    salary_max=raw.salary_max,
                    salary_currency=raw.salary_currency,
                    salary_interval=raw.salary_interval,
                    description=raw.description,
                    skills=json.dumps([s for s in raw.skills if isinstance(s, str)]),
                    seniority_level=raw.seniority_level,
                    employment_type=raw.employment_type,
                    is_remote=raw.is_remote,
                    board=raw.board,
                    job_url=raw.job_url,
                    posted_at=raw.posted_at,
                ))

            if not new_jobs:
                return 0

            async with AsyncSessionLocal() as db:
                for job in new_jobs:
                    db.add(job)
                session_obj = await db.get(ScrapeSession, session_id)
                if session_obj:
                    total_saved += len(new_jobs)
                    session_obj.job_count = total_saved
                await db.commit()

            logger.info("[%s] saved %d new jobs (total %d)", board_name, len(new_jobs), total_saved)
            return len(new_jobs)

    # Run all boards concurrently; each writes as it finishes
    await asyncio.gather(*[_scrape_and_save(b) for b in enabled_boards])

    # Finalise session
    async with AsyncSessionLocal() as db:
        session_obj = await db.get(ScrapeSession, session_id)
        if session_obj:
            session_obj.status = "done"
            session_obj.job_count = total_saved
            session_obj.finished_at = datetime.now(tz=timezone.utc)
            await db.commit()

    logger.info("Session %s complete: %d jobs", session_id, total_saved)
    return total_saved
