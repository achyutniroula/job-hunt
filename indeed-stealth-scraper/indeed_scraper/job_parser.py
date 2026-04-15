"""
job_parser.py — Normalize raw Indeed job dicts into a clean schema.
"""

import re
from datetime import datetime, timezone
from typing import Any, Optional

from .it_classifier import classify_it_job, extract_level
from .logger import get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Public schema
# ---------------------------------------------------------------------------

JOB_FIELDS = (
    "job_id",
    "title",
    "company",
    "location",
    "salary",
    "description",
    "posted_date",
    "url",
    "employment_type",
    "remote",
    "company_rating",
    "level",
    "is_it_job",
    "it_confidence",
    "it_skills",
    "it_reason",
)


def _normalize_date(raw: Any) -> Optional[str]:
    """Convert Unix timestamp (int/ms) → 'YYYY-MM-DD'; pass relative strings through."""
    if raw is None:
        return None
    # Numeric value — treat as Unix timestamp
    if isinstance(raw, (int, float)):
        ts = float(raw)
        if ts > 9_999_999_999:   # milliseconds
            ts /= 1000
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        except (OSError, ValueError, OverflowError):
            return None
    s = str(raw).strip()
    if not s:
        return None
    # Pure-digit string long enough to be a Unix timestamp
    if s.isdigit() and len(s) >= 10:
        ts = int(s)
        if ts > 9_999_999_999:
            ts //= 1000
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        except (OSError, ValueError, OverflowError):
            pass
    return s  # relative string like "3 days ago" — keep as-is


def _strip_html(text: str) -> str:
    """Remove HTML tags and collapse whitespace."""
    if not text:
        return ""
    # Remove tags
    clean = re.sub(r"<[^>]+>", " ", text)
    # Collapse whitespace
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def _safe_get(data: dict, *keys: str, default: Any = None) -> Any:
    """Traverse nested dict safely; return default if any key is missing."""
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
        if current is None:
            return default
    return current


def _parse_salary(job: dict) -> Optional[str]:
    """
    Extract a human-readable salary string from various possible locations
    in the raw Indeed job dict.
    """
    # Indeed stores salary in multiple locations depending on the page type
    candidates: list[Any] = [
        _safe_get(job, "extractedSalary"),
        _safe_get(job, "salarySnippet", "text"),
        _safe_get(job, "salary"),
        _safe_get(job, "compensation"),
    ]
    for c in candidates:
        if c:
            if isinstance(c, dict):
                # extractedSalary format: {min, max, type}
                min_val = c.get("min")
                max_val = c.get("max")
                pay_type = c.get("type", "")
                if min_val and max_val:
                    return f"${min_val:,.0f}–${max_val:,.0f} {pay_type}".strip()
                if min_val:
                    return f"${min_val:,.0f}+ {pay_type}".strip()
            return str(c).strip() or None
    return None


def _parse_remote(job: dict) -> bool:
    """Return True if the job appears to be remote."""
    # Check known remote indicators
    remote_flag = _safe_get(job, "remoteWork")
    if remote_flag:
        return bool(remote_flag)

    location = str(_safe_get(job, "jobLocationCity", default="")).lower()
    location += str(_safe_get(job, "formattedLocation", default="")).lower()
    location += str(_safe_get(job, "jobLocation", default="")).lower()

    return "remote" in location


def _parse_employment_type(job: dict) -> Optional[str]:
    """Extract employment type (Full-time, Part-time, Contract, etc.)."""
    raw = _safe_get(job, "jobTypes")
    if isinstance(raw, list) and raw:
        return ", ".join(str(t) for t in raw)
    raw = _safe_get(job, "employmentType")
    if raw:
        return str(raw)
    return None


def parse_job(raw: dict) -> Optional[dict]:
    """
    Normalize a raw Indeed job dict into the canonical schema.
    Returns None (and logs a warning) if the job cannot be parsed.
    """
    try:
        job_id: Optional[str] = (
            raw.get("jobkey")
            or raw.get("jobKey")
            or raw.get("job_id")
            or None
        )
        if not job_id:
            log.warning("Skipping job with no ID: %s", list(raw.keys())[:5])
            return None

        title: Optional[str] = raw.get("title") or raw.get("normalizedTitle") or None
        company: Optional[str] = (
            raw.get("company")
            or _safe_get(raw, "employer", "name")
            or None
        )
        location: Optional[str] = (
            raw.get("formattedLocation")
            or raw.get("jobLocation")
            or raw.get("jobLocationCity")
            or None
        )

        description_raw: str = (
            raw.get("snippet")
            or raw.get("description")
            or raw.get("jobDescription")
            or ""
        )
        description = _strip_html(description_raw) or None

        posted_date: Optional[str] = _normalize_date(
            raw.get("pubDate")
            or raw.get("postedAt")
            or raw.get("formattedRelativeTime")
        )

        job_url: Optional[str] = None
        job_path = raw.get("link") or raw.get("viewJobLink") or raw.get("jobUrl")
        if job_path:
            if job_path.startswith("http"):
                job_url = job_path
            else:
                job_url = f"https://ca.indeed.com{job_path}"
        elif job_id:
            job_url = f"https://ca.indeed.com/viewjob?jk={job_id}"

        company_rating_raw = _safe_get(raw, "companyRating") or _safe_get(
            raw, "employer", "companyOverviewLink"
        )
        company_rating: Optional[float] = None
        if isinstance(company_rating_raw, (int, float)):
            company_rating = float(company_rating_raw)

        # Build metadata dict for Layer 4 of classifier
        meta = {}
        for key in ("jobTypes", "categoryLabel", "industry", "occupationCategory",
                    "jobCategory", "taxonomyAttributes"):
            val = raw.get(key)
            if val:
                meta[key] = val

        it_result = classify_it_job(
            title=title or "",
            description=description or "",
            metadata=meta,
        )

        return {
            "job_id":        job_id,
            "title":         title,
            "company":       company,
            "location":      location,
            "salary":        _parse_salary(raw),
            "description":   description,
            "posted_date":   posted_date,
            "url":           job_url,
            "employment_type": _parse_employment_type(raw),
            "remote":        _parse_remote(raw),
            "company_rating": company_rating,
            "level":         extract_level(title or ""),
            "is_it_job":     it_result["is_it"],
            "it_confidence": it_result["confidence"],
            "it_skills":     it_result["layers"]["skills"],
            "it_reason":     it_result["reason"],
        }

    except Exception as exc:  # noqa: BLE001
        log.warning("Failed to parse job — skipping. Reason: %s | raw keys: %s", exc, list(raw.keys())[:8])
        return None


def parse_jobs(raw_jobs: list[dict]) -> list[dict]:
    """Parse a list of raw job dicts; silently skip unparseable entries."""
    parsed: list[dict] = []
    for raw in raw_jobs:
        job = parse_job(raw)
        if job:
            parsed.append(job)
    log.info(f"Parsed {len(parsed)}/{len(raw_jobs)} jobs successfully.")
    return parsed
