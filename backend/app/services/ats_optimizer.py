"""
ATS-friendly resume optimizer powered by Claude.

Strategy:
  - Feed Claude the full resume text + target job description
  - Instruct it to rewrite content only (NOT layout/template)
  - Return optimized text + a diff summary of changes
  - Never hallucinate: only facts from the original resume
"""
from __future__ import annotations

import logging
import re

import anthropic

from app.core.config import get_settings
from app.schemas.resume import ATSOptimizeResponse

logger = logging.getLogger(__name__)
settings = get_settings()

_SYSTEM_PROMPT = """\
You are a world-class resume writer and ATS optimization expert with 15+ years of experience \
helping candidates land interviews at top companies.

Your task is to rewrite a candidate's resume to maximize ATS (Applicant Tracking System) \
compatibility and interview conversion rate.

STRICT RULES — you MUST follow all of these:
1. NEVER invent experience, skills, companies, dates, or achievements that are not in the original.
2. NEVER change the structural layout — keep the same sections in the same order.
3. NEVER alter proper nouns (company names, school names, product names).
4. DO improve: action verbs, metric framing, keyword alignment, clarity, conciseness.
5. DO maximize keyword density for skills and tools mentioned in the job description.
6. DO replace weak verbs (helped, worked on, assisted) with strong verbs (engineered, architected, \
delivered, spearheaded).
7. DO quantify achievements wherever the original mentions numbers or scale.
8. Keep the tone professional but human — not robotic or generic.
9. Output ONLY the rewritten resume text, then a separator line "---CHANGES---", then a \
bullet-point list of the key changes you made.
"""

_USER_TEMPLATE = """\
## ORIGINAL RESUME:
{resume_text}

## TARGET JOB DESCRIPTION:
{job_description}

Rewrite the resume to maximally align with this job posting. \
Remember: same facts, better framing and keywords.
"""


def _estimate_ats_score(resume_text: str, job_description: str) -> int:
    """
    Very rough heuristic ATS score (0-100) based on keyword overlap.
    Used to show before/after comparison — not a real ATS simulation.
    """
    if not job_description:
        return 50
    import re as _re

    jd_words = set(_re.findall(r"\b[a-zA-Z]{4,}\b", job_description.lower()))
    res_words = set(_re.findall(r"\b[a-zA-Z]{4,}\b", resume_text.lower()))
    stopwords = {
        "with", "that", "this", "have", "from", "will", "your", "their",
        "they", "also", "must", "able", "work", "team", "role", "position",
    }
    jd_keywords = jd_words - stopwords
    if not jd_keywords:
        return 50
    overlap = len(jd_keywords & res_words) / len(jd_keywords)
    return min(100, int(overlap * 130))  # scale to be realistic-ish


async def optimize_resume(
    resume_text: str,
    job_description: str,
) -> ATSOptimizeResponse:
    """
    Call Claude to rewrite the resume for ATS optimization.
    Returns original + optimized text + change summary.
    """
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    user_message = _USER_TEMPLATE.format(
        resume_text=resume_text[:6000],       # stay within context
        job_description=job_description[:3000],
    )

    try:
        message = await client.messages.create(
            model=settings.anthropic_model,
            max_tokens=4096,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
    except anthropic.APIError as exc:
        logger.error("Anthropic API error during ATS optimization: %s", exc)
        raise

    full_response = message.content[0].text if message.content else ""

    # Split on separator
    if "---CHANGES---" in full_response:
        parts = full_response.split("---CHANGES---", 1)
        optimized_text = parts[0].strip()
        changes_raw = parts[1].strip()
    else:
        optimized_text = full_response.strip()
        changes_raw = ""

    # Parse bullet points from changes section
    changes: list[str] = []
    for line in changes_raw.splitlines():
        line = line.strip().lstrip("•-*").strip()
        if line:
            changes.append(line)

    score_before = _estimate_ats_score(resume_text, job_description)
    score_after  = _estimate_ats_score(optimized_text, job_description)

    return ATSOptimizeResponse(
        original_text=resume_text,
        optimized_text=optimized_text,
        changes_summary=changes,
        ats_score_before=score_before,
        ats_score_after=score_after,
    )
