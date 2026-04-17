"""AI-powered job fit analysis via Groq. Grades every job — no filtering."""
from __future__ import annotations

import asyncio
import logging
import re

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
_MODEL = "llama-3.3-70b-versatile"

_SYSTEM = (
    "You evaluate job fit for a software engineering candidate.\n"
    "Grade honestly and calibrate to real hiring standards.\n"
    "Reply ONLY in this exact format with no extra text:\n\n"
    "GRADE: [A/B/C/D/F with optional +/-]\n"
    "SUMMARY: [one honest sentence]\n"
    "STRENGTHS: [strength 1] | [strength 2] | [strength 3]\n"
    "GAPS: [gap 1] | [gap 2] | [gap 3]\n"
    "TIP: [one sentence — what to highlight in cover letter for this specific role]\n\n"
    "Use fewer pipe items if not applicable. Never add extra lines."
)

# ── Section extraction ────────────────────────────────────────────────────────

REQUIREMENTS_TRIGGERS = [
    "requirement", "qualification", "what you'll need", "what we're looking for",
    "what you bring", "you have", "you will have", "you should have",
    "you must have", "must have", "must-have", "basic qualifications",
    "minimum qualifications", "preferred qualifications", "nice to have",
    "nice-to-have", "skills required", "skills we're looking for",
    "experience required", "experience we're looking for",
    "about you", "who you are", "what you need", "technical requirements",
    "technical skills", "key skills", "core skills", "competencies",
    "the ideal candidate", "we are looking for", "we're looking for",
    "successful candidate", "you will need",
]

STOP_TRIGGERS = [
    "what we offer", "what we provide", "we offer", "benefits",
    "perks", "compensation", "salary", "pay range", "total rewards",
    "about us", "about the company", "our culture",
    "why join", "why work", "equal opportunity", "diversity",
    "accommodation", "accessibility", "application process",
    "how to apply", "next steps",
]


def extract_requirements(jd: str) -> str:
    lines = jd.splitlines()
    start = None
    for i, line in enumerate(lines):
        stripped = line.strip().lower()
        if any(t in stripped for t in REQUIREMENTS_TRIGGERS):
            start = i
            break

    if start is None:
        return jd[:1500]

    end = len(lines)
    for i, line in enumerate(lines[start + 1:], start + 1):
        stripped = line.strip().lower()
        if any(t in stripped for t in STOP_TRIGGERS):
            end = i
            break

    section = "\n".join(lines[start:end]).strip()
    if len(section) < 80:
        return jd[:1500]
    return section[:1500]


# ── Seniority / user level detection ─────────────────────────────────────────

def detect_seniority(job_title: str, job_description: str) -> str:
    """Returns: 'junior' | 'mid' | 'senior' | 'lead' | 'any'"""
    text = (job_title + " " + job_description[:300]).lower()
    if any(w in text for w in ["principal", "staff", "vp ", "director", "head of", "architect"]):
        return "lead"
    if any(w in text for w in ["senior", "sr.", "sr ", "lead ", "8+ years", "7+ years", "6+ years"]):
        return "senior"
    if any(w in text for w in ["junior", "jr.", "jr ", "entry", "entry-level", "new grad",
                                "graduate", "intern", "0-2 years", "1-2 years", "1+ year"]):
        return "junior"
    if any(w in text for w in ["mid ", "mid-level", "intermediate", "3-5 years", "2-4 years"]):
        return "mid"
    return "any"


def detect_user_level(resume_text: str) -> str:
    """Returns: 'student' | 'junior' | 'mid' | 'senior'"""
    text = resume_text.lower()
    years_exp = _estimate_years(text)
    if any(w in text for w in ["currently enrolled", "bachelor", "bsc", "b.sc", "honours",
                                "expected graduation", "gpa", "university"]):
        if years_exp < 2:
            return "student"
    if years_exp < 2:
        return "junior"
    if years_exp < 5:
        return "mid"
    return "senior"


def _estimate_years(text: str) -> int:
    years = re.findall(r"20\d{2}", text)
    return len(set(years)) // 2 if years else 0


# ── Response parser ───────────────────────────────────────────────────────────

_SAFE_DEFAULTS: dict = {
    "grade": "?",
    "summary": "Could not evaluate",
    "strengths": [],
    "gaps": [],
    "tip": "Apply anyway",
}


def _parse_fit_response(text: str, seniority: str, user_level: str) -> dict:
    result: dict = {**_SAFE_DEFAULTS, "seniority": seniority, "user_level": user_level}
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("GRADE:"):
            result["grade"] = line[6:].strip()
        elif line.startswith("SUMMARY:"):
            result["summary"] = line[8:].strip()
        elif line.startswith("STRENGTHS:"):
            parts = [p.strip() for p in line[10:].split("|") if p.strip()]
            result["strengths"] = parts[:3]
        elif line.startswith("GAPS:"):
            parts = [p.strip() for p in line[5:].split("|") if p.strip()]
            result["gaps"] = parts[:3]
        elif line.startswith("TIP:"):
            result["tip"] = line[4:].strip()
    return result


# ── Main analyze functions ────────────────────────────────────────────────────

async def analyze_fit(
    resume_text: str,
    job_title: str,
    job_description: str,
    archetype: str = "Software Developer",
    semantic_score: float = 0.0,
) -> dict:
    """Grades every job — no filtering, no None returns."""
    jd_requirements = extract_requirements(job_description)
    job_seniority = detect_seniority(job_title, job_description)
    user_level = detect_user_level(resume_text)

    api_key = get_settings().groq_api_key
    if not api_key:
        return {**_SAFE_DEFAULTS, "seniority": job_seniority, "user_level": user_level}

    user_msg = (
        f"Candidate level: {user_level}\n"
        f"Role: {job_title} ({archetype}, {job_seniority} level)\n"
        f"Semantic match score: {semantic_score:.0%}\n\n"
        f"=== RESUME (first 400 chars) ===\n{resume_text[:400]}\n\n"
        f"=== JOB REQUIREMENTS ===\n{jd_requirements}"
    )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                _GROQ_URL,
                json={
                    "model": _MODEL,
                    "messages": [
                        {"role": "system", "content": _SYSTEM},
                        {"role": "user", "content": user_msg},
                    ],
                    "max_tokens": 220,
                    "temperature": 0.3,
                },
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )
        if resp.status_code == 429:
            await asyncio.sleep(10)
            async with httpx.AsyncClient(timeout=30.0) as client2:
                resp = await client2.post(
                    _GROQ_URL,
                    json={
                        "model": _MODEL,
                        "messages": [
                            {"role": "system", "content": _SYSTEM},
                            {"role": "user", "content": user_msg},
                        ],
                        "max_tokens": 220,
                        "temperature": 0.3,
                    },
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                )
        if resp.status_code != 200:
            logger.warning("Fit analysis Groq call failed: %s", resp.status_code)
            return {**_SAFE_DEFAULTS, "seniority": job_seniority, "user_level": user_level}

        text = resp.json()["choices"][0]["message"]["content"]
        return _parse_fit_response(text, job_seniority, user_level)

    except Exception as exc:
        logger.warning("analyze_fit failed for '%s': %s", job_title, exc)
        return {**_SAFE_DEFAULTS, "seniority": job_seniority, "user_level": user_level}


async def analyze_all_jobs(
    jobs: list[dict],
    resume_text: str,
    batch_size: int = 25,
    delay_between_batches: float = 62.0,
) -> list[dict]:
    """
    Grades every job in the list. No jobs are filtered out.
    Runs in batches to respect Groq free-tier rate limits (~30 req/min).
    Returns full list with fit_analysis set on every job.
    """
    total = len(jobs)
    logger.info("Grading %d jobs for fit...", total)
    graded = 0
    result_map: dict[int, dict] = {}

    batches = [jobs[i:i + batch_size] for i in range(0, total, batch_size)]

    for batch_idx, batch in enumerate(batches):
        tasks = [
            analyze_fit(
                resume_text=resume_text,
                job_title=j.get("title", ""),
                job_description=j.get("description", ""),
                archetype=j.get("archetype", "Software Developer"),
                semantic_score=j.get("match_score") or 0.0,
            )
            for j in batch
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, (job, res) in enumerate(zip(batch, results)):
            idx = batch_idx * batch_size + i
            if isinstance(res, Exception):
                logger.warning("Fit analysis error for job %d: %s", idx, res)
                jd = job.get("description", "")
                title = job.get("title", "")
                result_map[idx] = {
                    **_SAFE_DEFAULTS,
                    "seniority": detect_seniority(title, jd),
                    "user_level": detect_user_level(resume_text),
                }
            else:
                result_map[idx] = res
            graded += 1

        logger.info("Batch %d/%d complete (%d jobs graded so far)", batch_idx + 1, len(batches), graded)

        if batch_idx < len(batches) - 1:
            await asyncio.sleep(delay_between_batches)

    for i, job in enumerate(jobs):
        job["fit_analysis"] = result_map.get(i, {**_SAFE_DEFAULTS,
                                                  "seniority": "any", "user_level": "mid"})

    return jobs
