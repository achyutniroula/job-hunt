"""
routes/results.py — GET /api/results  (paginated, filtered)

Reads from in-memory shared state. If memory is empty (e.g. after a server
restart), falls back to the most recent JSON file in the output directory.
"""

import json
from pathlib import Path

from fastapi import APIRouter, Query

from indeed_scraper.api.scrape_runner import get_jobs

router = APIRouter()

_OUTPUT_DIR = Path("output")


def _load_from_latest_file() -> list[dict]:
    """Return jobs from the newest JSON file in the output directory."""
    if not _OUTPUT_DIR.exists():
        return []
    files = sorted(_OUTPUT_DIR.glob("jobs_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return []
    try:
        return json.loads(files[0].read_text(encoding="utf-8"))
    except Exception:
        return []


@router.get("/results")
async def get_results(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=200, ge=1, le=10000),
    location: str = Query(default=""),
    company: str = Query(default=""),
    remote: str = Query(default=""),   # "true" | "false" | ""
    salary: str = Query(default=""),   # non-empty → only jobs with salary
) -> dict:
    """Return a paginated, filtered slice of the job list."""
    jobs = get_jobs()

    # Fall back to latest saved file if memory is empty (post-restart)
    if not jobs:
        jobs = _load_from_latest_file()

    print(f"[DEBUG /api/results] in-memory jobs: {len(jobs)}", flush=True)

    if location:
        loc_lower = location.lower()
        jobs = [j for j in jobs if loc_lower in (j.get("location") or "").lower()]

    if company:
        co_lower = company.lower()
        jobs = [j for j in jobs if co_lower in (j.get("company") or "").lower()]

    if remote == "true":
        jobs = [j for j in jobs if j.get("remote") is True]
    elif remote == "false":
        jobs = [j for j in jobs if not j.get("remote")]

    if salary:
        jobs = [j for j in jobs if j.get("salary")]

    total = len(jobs)
    offset = (page - 1) * limit

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": max(1, -(-total // limit)),
        "jobs": jobs[offset : offset + limit],
    }
