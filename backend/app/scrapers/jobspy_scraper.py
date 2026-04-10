"""
Wraps python-jobspy to scrape LinkedIn, Indeed, Glassdoor, ZipRecruiter,
and Google Jobs. Each board is exposed as its own BaseScraper subclass so
the orchestrator can enable/disable them individually.
"""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone

from app.scrapers.base import BaseScraper, RawJob

logger = logging.getLogger(__name__)

# JobSpy board identifiers
_BOARD_MAP = {
    "linkedin": "linkedin",
    "indeed": "indeed",
    "glassdoor": "glassdoor",
    "ziprecruiter": "zip_recruiter",
    "google": "google",
}


def _str(val) -> str | None:
    """Convert a pandas/jobspy value to str, returning None for NaN/empty."""
    if val is None:
        return None
    if isinstance(val, float):   # catches float('nan') — truthy but not a string
        return None
    s = str(val).strip()
    return s or None


def _parse_salary(job_row) -> tuple[float | None, float | None, str | None, str | None]:
    """Extract salary fields from a JobSpy DataFrame row."""
    try:
        lo = float(job_row.get("min_amount") or 0) or None
        hi = float(job_row.get("max_amount") or 0) or None
        currency = job_row.get("currency") or "CAD"
        interval = job_row.get("interval")
        return lo, hi, currency, interval
    except Exception:
        return None, None, "CAD", None


def _extract_skills(description: str | None) -> list[str]:
    """Very lightweight keyword extractor for common tech skills."""
    if not description:
        return []
    SKILL_PATTERNS = re.compile(
        r"\b(Python|Java|JavaScript|TypeScript|React|Vue|Angular|Node\.js|"
        r"FastAPI|Django|Flask|Spring|\.NET|C#|C\+\+|Go|Rust|Kotlin|Swift|"
        r"SQL|PostgreSQL|MySQL|MongoDB|Redis|Elasticsearch|Kafka|RabbitMQ|"
        r"Docker|Kubernetes|AWS|Azure|GCP|Terraform|Ansible|CI/CD|Git|"
        r"Machine Learning|Deep Learning|NLP|LLM|PyTorch|TensorFlow|"
        r"REST|GraphQL|gRPC|Microservices|Agile|Scrum|Linux|Bash)\b",
        re.IGNORECASE,
    )
    return list({m.group() for m in SKILL_PATTERNS.finditer(description)})


def _infer_seniority(title: str) -> str | None:
    title_l = title.lower()
    if any(w in title_l for w in ("intern", "internship", "co-op", "coop")):
        return "internship"
    if any(w in title_l for w in ("junior", "jr.", "entry")):
        return "junior"
    if any(w in title_l for w in ("senior", "sr.", "staff", "principal", "lead")):
        return "senior"
    if any(w in title_l for w in ("director", "vp ", "vice president", "head of", "cto", "ceo")):
        return "executive"
    return "mid"


def _jobspy_row_to_raw(row, board: str) -> RawJob:
    title = str(row.get("title") or "Unknown")
    desc = str(row.get("description") or "")
    lo, hi, currency, interval = _parse_salary(row)
    raw_date = row.get("date_posted")
    posted = None
    if raw_date:
        try:
            posted = datetime.combine(raw_date, datetime.min.time()).replace(
                tzinfo=timezone.utc
            )
        except Exception:
            pass

    return RawJob(
        title=title,
        board=board,
        company=_str(row.get("company")),
        location=_str(row.get("location")),
        description=desc or None,
        salary_min=lo,
        salary_max=hi,
        salary_currency=currency,
        salary_interval=interval,
        skills=_extract_skills(desc),
        seniority_level=_infer_seniority(title),
        employment_type=_str(row.get("job_type")),
        is_remote=bool(row.get("is_remote")),
        job_url=_str(row.get("job_url")),
        posted_at=posted,
    )


class JobSpyScraper(BaseScraper):
    """Single scraper that calls jobspy for one board."""

    def __init__(self, board_key: str):
        self.board_key = board_key          # e.g. "linkedin"
        self.board_name = board_key

    async def scrape(
        self,
        keywords: str,
        location: str,
        remote_only: bool = False,
        max_results: int = 25,
    ) -> list[RawJob]:
        jobspy_site = _BOARD_MAP.get(self.board_key)
        if not jobspy_site:
            return []

        try:
            # jobspy is synchronous; run in thread pool
            jobs = await asyncio.to_thread(
                self._sync_scrape,
                jobspy_site,
                keywords,
                location,
                remote_only,
                max_results,
            )
            return jobs
        except Exception as exc:
            logger.warning("JobSpy [%s] failed: %s", self.board_key, exc)
            return []

    def _sync_scrape(
        self,
        site: str,
        keywords: str,
        location: str,
        remote_only: bool,
        max_results: int,
    ) -> list[RawJob]:
        from jobspy import scrape_jobs  # type: ignore

        df = scrape_jobs(
            site_name=[site],
            search_term=keywords,
            location=location,
            results_wanted=max_results,
            is_remote=remote_only,
            country_indeed="Canada",
            linkedin_fetch_description=(site == "linkedin"),
        )
        if df is None or df.empty:
            return []

        results = []
        for _, row in df.iterrows():
            try:
                results.append(_jobspy_row_to_raw(row.to_dict(), self.board_key))
            except Exception as e:
                logger.debug("Row parse error [%s]: %s", self.board_key, e)
        return results


# Convenience: one instance per supported board
LinkedInScraper = lambda: JobSpyScraper("linkedin")      # noqa: E731
IndeedScraper = lambda: JobSpyScraper("indeed")          # noqa: E731
GlassdoorScraper = lambda: JobSpyScraper("glassdoor")    # noqa: E731
ZipRecruiterScraper = lambda: JobSpyScraper("ziprecruiter")  # noqa: E731
GoogleJobsScraper = lambda: JobSpyScraper("google")      # noqa: E731
