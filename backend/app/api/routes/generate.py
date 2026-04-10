"""
Generate API routes.

POST /api/generate/optimize     — ATS resume optimization
POST /api/generate/cover-letter — cover letter generation
POST /api/generate/fetch-url    — fetch job description from a posting URL
"""
from __future__ import annotations

import asyncio
import logging
import os
import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select

from app.core.config import get_settings
from app.schemas.resume import (
    ATSOptimizeRequest,
    ATSOptimizeResponse,
    CoverLetterRequest,
    CoverLetterResponse,
)
from app.services.ats_optimizer import optimize_resume, optimize_with_profile
from app.services.github_ingestion import fetch_github_profile
from app.services.linkedin_ingestion import fetch_linkedin_profile
from app.services.skill_inference import infer_skill_profile
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
    """Rewrite a resume to maximize ATS compatibility. Supports re-optimization loop."""
    if not settings.anthropic_api_key:
        raise HTTPException(503, "Anthropic API key not configured.")

    # Re-optimization: use previous optimized text instead of re-parsing file
    if body.previous_optimized:
        resume_text = body.previous_optimized
        pass_num = 2
    else:
        resume_text = await _load_resume_text(body.resume_filename)
        pass_num = 1

    job_desc = await _get_job_description(body.job_id, body.job_description)

    if not job_desc.strip():
        raise HTTPException(400, "Provide either job_id or job_description.")

    try:
        if body.github_urls and pass_num == 1:
            # Concurrent ingestion
            github_tasks = [fetch_github_profile(u) for u in body.github_urls[:3]]
            linkedin_task = (
                fetch_linkedin_profile(body.linkedin_url)
                if body.linkedin_url else None
            )
            gathered = await asyncio.gather(
                *github_tasks,
                *([] if linkedin_task is None else [linkedin_task]),
                return_exceptions=True,
            )
            github_profiles = [g for g in gathered[:len(github_tasks)]
                               if not isinstance(g, Exception) and g is not None]
            github_profile = github_profiles[0] if github_profiles else None
            linkedin_profile = (
                gathered[len(github_tasks)]
                if linkedin_task and not isinstance(gathered[len(github_tasks)], Exception)
                else None
            )
            skill_profile = infer_skill_profile(github_profile, linkedin_profile)
            result = await optimize_with_profile(
                resume_text=resume_text,
                job_description=job_desc,
                skill_profile=skill_profile,
                github_profile=github_profile,
                linkedin_profile=linkedin_profile,
            )
        else:
            result = await optimize_resume(
                resume_text=resume_text,
                job_description=job_desc,
                previous_improvements=body.previous_improvements or None,
                pass_num=pass_num,
            )
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


# ── Cover letter .docx export ────────────────────────────────────────────────

class DocxRequest(BaseModel):
    text: str
    company: str = "company"


@router.post("/cover-letter-docx")
async def cover_letter_docx(body: DocxRequest):
    """Convert cover letter text to a Word .docx file."""
    try:
        import io
        from docx import Document
        from docx.shared import Pt, Inches
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        doc = Document()

        # Page margins
        for section in doc.sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1.25)
            section.right_margin = Inches(1.25)

        # Body style
        style = doc.styles["Normal"]
        style.font.name = "Calibri"
        style.font.size = Pt(11)

        for para_text in body.text.split("\n"):
            p = doc.add_paragraph(para_text)
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            pf = p.paragraph_format
            pf.space_after = Pt(6)

        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)

        safe = body.company.replace(" ", "_").replace("/", "_")[:40]
        filename = f"cover_letter_{safe}.docx"
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as exc:
        raise HTTPException(500, f"Failed to generate .docx: {exc}")


# ── Job URL fetcher ───────────────────────────────────────────────────────────

class FetchUrlRequest(BaseModel):
    url: str


class FetchUrlResponse(BaseModel):
    title: str | None = None
    company: str | None = None
    description: str
    source: str


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-CA,en-US;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

_INDEED_HEADERS = {
    **_HEADERS,
    "Referer": "https://ca.indeed.com/",
    "Origin": "https://ca.indeed.com",
}

_LINKEDIN_HEADERS = {
    **_HEADERS,
    "Referer": "https://www.linkedin.com/jobs/",
}

# Board-specific CSS selectors for job description container
_BOARD_SELECTORS: dict[str, list[str]] = {
    "indeed":       ["#jobDescriptionText", ".jobsearch-jobDescriptionText"],
    "linkedin":     [".description__text", ".show-more-less-html__markup"],
    "glassdoor":    [".JobDetails_jobDescription__uW_fK", "[class*='jobDescription']"],
    "ziprecruiter": [".job_description", "[class*='jobDescription']"],
    "jobbank":      ["#job-detail-1", ".job-posting-detail"],
    "eluta":        [".job-description", ".description"],
    "google":       [".YgLbBe", "[class*='description']"],
}

_TITLE_SELECTORS = [
    "h1.jobTitle", "h1[class*='title']", "h1[class*='Title']",
    ".job-title", ".jobTitle", "h1",
]
_COMPANY_SELECTORS = [
    "[class*='companyName']", "[class*='company-name']", "[data-company-name]",
    ".company", ".employer",
]


def _detect_board(url: str) -> str:
    url_l = url.lower()
    for board in _BOARD_SELECTORS:
        if board in url_l:
            return board
    if "ca.indeed" in url_l or "indeed.com" in url_l:
        return "indeed"
    return "unknown"


def _extract_text(soup, selectors: list[str]) -> str | None:
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            return el.get_text(" ", strip=True)
    return None


@router.post("/fetch-url", response_model=FetchUrlResponse)
async def fetch_job_url(body: FetchUrlRequest):
    """Fetch job description from a posting URL on any supported job board."""
    import httpx
    from bs4 import BeautifulSoup

    url = body.url.strip()
    if not url.startswith("http"):
        raise HTTPException(400, "Invalid URL")

    board = _detect_board(url)

    headers = (
        _INDEED_HEADERS if "indeed" in url.lower()
        else _LINKEDIN_HEADERS if "linkedin" in url.lower()
        else _HEADERS
    )

    try:
        async with httpx.AsyncClient(
            headers=headers, follow_redirects=True, timeout=25.0
        ) as client:
            resp = await client.get(url)
            if resp.status_code in (403, 429, 999):
                raise HTTPException(
                    422,
                    "This job board blocked automated access (403/429). "
                    "Please paste the job description manually."
                )
            resp.raise_for_status()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, f"Could not fetch URL: {exc}")

    soup = BeautifulSoup(resp.text, "lxml")

    # Remove script/style noise
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()

    # Try board-specific selectors first
    desc = None
    selectors = _BOARD_SELECTORS.get(board, [])
    if selectors:
        desc = _extract_text(soup, selectors)

    # Generic fallback: find the largest <div> or <section> by text length
    if not desc:
        candidates = soup.find_all(["div", "section", "article"], recursive=True)
        best = max(candidates, key=lambda t: len(t.get_text()), default=None)
        if best:
            desc = best.get_text(" ", strip=True)

    if not desc or len(desc) < 50:
        raise HTTPException(422, "Could not extract job description from URL. Try pasting the description manually.")

    title = _extract_text(soup, _TITLE_SELECTORS)
    company = _extract_text(soup, _COMPANY_SELECTORS)

    # Clean up excessive whitespace
    desc = re.sub(r"\s{3,}", "\n\n", desc)[:8000]

    return FetchUrlResponse(title=title, company=company, description=desc, source=board)
