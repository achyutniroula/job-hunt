"""
Generate API routes.

POST /api/generate/optimize     — ATS resume optimization
POST /api/generate/cover-letter — cover letter generation
"""
from __future__ import annotations

import logging
import os

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.core.config import get_settings
from app.schemas.resume import (
    ATSOptimizeRequest,
    ATSOptimizeResponse,
    CoverLetterRequest,
    CoverLetterResponse,
)
from app.services.ats_optimizer import optimize_resume
from app.services.cover_letter import generate_cover_letter
from app.services.resume_parser import parse_resume

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


async def _load_resume_text(filename: str) -> str:
    path = os.path.join(settings.upload_dir, filename)
    if not os.path.exists(path):
        raise HTTPException(404, f"Resume '{filename}' not found. Upload it first.")
    with open(path, "rb") as f:
        raw = f.read()
    try:
        parsed = parse_resume(raw, filename)
        return parsed.raw_text
    except Exception as exc:
        raise HTTPException(422, f"Could not parse resume: {exc}")


async def _get_job_description(job_id: str | None, job_description: str | None) -> str:
    """Resolve job description from job_id or raw text."""
    if job_description:
        return job_description

    if job_id:
        from app.core.database import AsyncSessionLocal
        from app.models.job import Job

        async with AsyncSessionLocal() as db:
            job = await db.get(Job, job_id)
            if not job:
                raise HTTPException(404, f"Job '{job_id}' not found")
            return job.description or ""

    return ""


@router.post("/optimize", response_model=ATSOptimizeResponse)
async def ats_optimize(body: ATSOptimizeRequest):
    """
    Rewrite a resume to maximize ATS compatibility for a target job.
    """
    if not settings.anthropic_api_key:
        raise HTTPException(503, "Anthropic API key not configured.")

    resume_text = await _load_resume_text(body.resume_filename)
    job_desc = await _get_job_description(body.job_id, body.job_description)

    if not job_desc.strip():
        raise HTTPException(
            400,
            "Provide either job_id (to look up a scraped job) or job_description.",
        )

    try:
        result = await optimize_resume(resume_text=resume_text, job_description=job_desc)
    except Exception as exc:
        logger.error("ATS optimization failed: %s", exc)
        raise HTTPException(500, f"Optimization failed: {exc}")

    return result


@router.post("/cover-letter", response_model=CoverLetterResponse)
async def cover_letter(body: CoverLetterRequest):
    """
    Generate a human-sounding cover letter tailored to a job posting.
    """
    if not settings.anthropic_api_key:
        raise HTTPException(503, "Anthropic API key not configured.")

    resume_text = await _load_resume_text(body.resume_filename)
    job_desc = await _get_job_description(body.job_id, body.job_description)

    # Resolve company + title from job_id if not provided
    company = body.company_name
    title = body.job_title
    if body.job_id and (not company or not title):
        from app.core.database import AsyncSessionLocal
        from app.models.job import Job

        async with AsyncSessionLocal() as db:
            job = await db.get(Job, body.job_id)
            if job:
                company = company or job.company or "the company"
                title = title or job.title or "the role"

    try:
        result = await generate_cover_letter(
            resume_text=resume_text,
            job_title=title or "the role",
            company_name=company or "the company",
            job_description=job_desc,
            extra_notes=body.extra_notes,
        )
    except Exception as exc:
        logger.error("Cover letter generation failed: %s", exc)
        raise HTTPException(500, f"Generation failed: {exc}")

    return result
