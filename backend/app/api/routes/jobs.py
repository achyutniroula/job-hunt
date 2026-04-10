"""
Jobs API routes.

POST /api/jobs/scrape     — kick off a new scrape session (async background task)
GET  /api/jobs/session/{id} — poll session status
GET  /api/jobs/{session_id} — list jobs for a session (with filters)
POST /api/jobs/{session_id}/match — re-score jobs against an uploaded resume
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.job import Job
from app.models.session import ScrapeSession
from app.schemas.job import (
    JobFilter,
    JobRead,
    ScrapeRequest,
    ScrapeSessionRead,
)
from app.scrapers.orchestrator import run_scrape_session
from app.services.matcher import score_jobs_for_resume
from app.services.resume_parser import parse_resume
from app.core.config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


@router.post("/scrape", response_model=ScrapeSessionRead, status_code=202)
async def start_scrape(
    body: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Kick off a multi-board scrape in the background.
    Returns the session record immediately; poll /session/{id} for status.
    """
    session = ScrapeSession(
        id=str(uuid.uuid4()),
        keywords=body.keywords,
        location=body.location,
        remote_only=body.remote_only,
        boards=json.dumps(body.boards) if body.boards else None,
        status="pending",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    # Run scrape asynchronously
    background_tasks.add_task(
        _scrape_in_background,
        session_id=session.id,
        keywords=body.keywords,
        location=body.location,
        remote_only=body.remote_only,
        boards=body.boards,
    )

    return _session_to_schema(session)


async def _scrape_in_background(
    session_id: str,
    keywords: str,
    location: str,
    remote_only: bool,
    boards: list[str] | None,
):
    """Background task: orchestrator manages its own DB sessions per board."""
    from app.core.database import AsyncSessionLocal

    try:
        await run_scrape_session(
            session_id=session_id,
            keywords=keywords,
            location=location,
            remote_only=remote_only,
            boards=boards,
        )
    except Exception as exc:
        logger.error("Scrape session %s failed: %s", session_id, exc)
        async with AsyncSessionLocal() as db:
            session = await db.get(ScrapeSession, session_id)
            if session:
                session.status = "failed"
                session.error = str(exc)
                session.finished_at = datetime.now(tz=timezone.utc)
                await db.commit()


@router.get("/session/{session_id}", response_model=ScrapeSessionRead)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(ScrapeSession, session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return _session_to_schema(session)


@router.get("/{session_id}", response_model=list[JobRead])
async def list_jobs(
    session_id: str,
    min_score: float | None = Query(None),
    remote_only: bool | None = Query(None),
    boards: str | None = Query(None, description="Comma-separated board names"),
    seniority: str | None = Query(None, description="Comma-separated seniority levels"),
    sort_by: str = Query("match_score", regex="^(match_score|posted_at)$"),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Return jobs for a session, with optional filters."""
    stmt = select(Job).where(Job.session_id == session_id)

    if min_score is not None:
        stmt = stmt.where(Job.match_score >= min_score)
    if remote_only:
        stmt = stmt.where(Job.is_remote == True)  # noqa: E712
    if boards:
        board_list = [b.strip() for b in boards.split(",")]
        stmt = stmt.where(Job.board.in_(board_list))
    if seniority:
        seniority_list = [s.strip() for s in seniority.split(",")]
        stmt = stmt.where(Job.seniority_level.in_(seniority_list))

    if sort_by == "match_score":
        stmt = stmt.order_by(Job.match_score.desc().nullslast())
    else:
        stmt = stmt.order_by(Job.posted_at.desc().nullslast())

    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    jobs = result.scalars().all()
    return [_job_to_schema(j) for j in jobs]


@router.post("/{session_id}/match", response_model=list[JobRead])
async def match_jobs_to_resume(
    session_id: str,
    resume_filename: str = Query(..., description="Filename from /api/resume/upload"),
    db: AsyncSession = Depends(get_db),
):
    """Score all jobs in a session against a previously uploaded resume."""
    import os

    resume_path = os.path.join(settings.upload_dir, resume_filename)
    if not os.path.exists(resume_path):
        raise HTTPException(404, "Resume file not found — upload it first.")

    with open(resume_path, "rb") as f:
        file_bytes = f.read()

    parsed = parse_resume(file_bytes, resume_filename)

    # Fetch all jobs for session
    result = await db.execute(select(Job).where(Job.session_id == session_id))
    jobs = list(result.scalars().all())

    if not jobs:
        raise HTTPException(404, "No jobs found for this session")

    # Score + sort
    scored_jobs = await score_jobs_for_resume(parsed, jobs)

    # Persist scores
    for job in scored_jobs:
        db_job = await db.get(Job, job.id)
        if db_job:
            db_job.match_score = job.match_score

    # Update session resume reference
    session = await db.get(ScrapeSession, session_id)
    if session:
        session.resume_filename = resume_filename
    await db.commit()

    return [_job_to_schema(j) for j in scored_jobs]


@router.get("/detail/{job_id}", response_model=JobRead)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return _job_to_schema(job)


# ── helpers ───────────────────────────────────────────────────────────────────

def _job_to_schema(job: Job) -> JobRead:
    skills_raw = job.skills or "[]"
    try:
        skills = json.loads(skills_raw)
    except Exception:
        skills = []
    return JobRead(
        id=job.id,
        session_id=job.session_id,
        title=job.title,
        company=job.company,
        location=job.location,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        salary_currency=job.salary_currency,
        salary_interval=job.salary_interval,
        description=job.description,
        skills=skills,
        seniority_level=job.seniority_level,
        employment_type=job.employment_type,
        is_remote=job.is_remote or False,
        board=job.board,
        job_url=job.job_url,
        posted_at=job.posted_at,
        match_score=job.match_score,
        created_at=job.created_at,
    )


def _session_to_schema(s: ScrapeSession) -> ScrapeSessionRead:
    boards = None
    if s.boards:
        try:
            boards = json.loads(s.boards)
        except Exception:
            boards = None
    return ScrapeSessionRead(
        id=s.id,
        keywords=s.keywords,
        location=s.location,
        remote_only=s.remote_only,
        boards=boards,
        status=s.status,
        job_count=s.job_count,
        error=s.error,
        resume_filename=s.resume_filename,
        created_at=s.created_at,
        finished_at=s.finished_at,
    )
