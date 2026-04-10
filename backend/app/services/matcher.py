"""
Semantic job-to-resume matching engine.

Combines:
  1. Sentence-transformer cosine similarity (semantic)
  2. Skill overlap score
  3. Seniority alignment score
  4. Keyword density score

Final score is a weighted sum → 0-100.
"""
from __future__ import annotations

import json
import logging
import re
from functools import lru_cache

from app.models.job import Job
from app.schemas.resume import ParsedResume

logger = logging.getLogger(__name__)

# Weights for score components
W_SEMANTIC   = 0.45
W_SKILL      = 0.35
W_SENIORITY  = 0.10
W_KEYWORD    = 0.10

SENIORITY_ORDER = ["internship", "junior", "mid", "senior", "lead", "executive"]


@lru_cache(maxsize=1)
def _get_model():
    """Load sentence-transformer model once, cache it."""
    from sentence_transformers import SentenceTransformer

    logger.info("Loading sentence-transformer model…")
    return SentenceTransformer("all-MiniLM-L6-v2")


def _cosine_sim(a, b) -> float:
    from numpy import dot
    from numpy.linalg import norm

    n = norm(a) * norm(b)
    if n == 0:
        return 0.0
    return float(dot(a, b) / n)


def _semantic_score(resume_text: str, job_desc: str | None) -> float:
    if not isinstance(job_desc, str) or not job_desc.strip():
        return 0.0
    try:
        model = _get_model()
        # Truncate to avoid OOM on huge descriptions
        r_trunc = resume_text[:2000]
        j_trunc = job_desc[:2000]
        embeddings = model.encode([r_trunc, j_trunc], convert_to_numpy=True)
        return max(0.0, _cosine_sim(embeddings[0], embeddings[1]))
    except Exception as exc:
        logger.warning("Semantic scoring failed: %s", exc)
        return 0.0


def _to_str_set(skills: list) -> set[str]:
    """Safely convert a skill list to a lowercase string set, skipping non-strings."""
    return {s.lower() for s in skills if isinstance(s, str)}


def _skill_overlap_score(resume_skills: list, job_skills: list) -> float:
    if not job_skills:
        return 0.5  # neutral if job has no extracted skills
    if not resume_skills:
        return 0.0
    rs = _to_str_set(resume_skills)
    js = _to_str_set(job_skills)
    if not js:
        return 0.5
    overlap = len(rs & js)
    return overlap / len(js)


def _seniority_score(resume_seniority: str | None, job_seniority: str | None) -> float:
    if not resume_seniority or not job_seniority:
        return 0.5
    try:
        ri = SENIORITY_ORDER.index(resume_seniority)
        ji = SENIORITY_ORDER.index(job_seniority)
        diff = abs(ri - ji)
        # 0 diff → 1.0, 1 diff → 0.7, 2 → 0.4, 3+ → 0.1
        return max(0.1, 1.0 - diff * 0.3)
    except ValueError:
        return 0.5


def _keyword_density_score(resume_text: str, job_desc: str | None) -> float:
    if not isinstance(job_desc, str) or not job_desc:
        return 0.0
    # Extract prominent words from JD (length > 4, not stopwords)
    STOPWORDS = {
        "the", "and", "for", "with", "that", "this", "have", "from",
        "will", "your", "are", "our", "you", "their", "they", "also",
        "must", "able", "work", "team", "role", "company", "position",
    }
    words = re.findall(r"\b[a-zA-Z]{5,}\b", job_desc.lower())
    jd_vocab = {w for w in words if w not in STOPWORDS}
    if not jd_vocab:
        return 0.0

    resume_lower = resume_text.lower()
    hits = sum(1 for w in jd_vocab if w in resume_lower)
    return min(1.0, hits / max(len(jd_vocab), 1))


# ── Public API ────────────────────────────────────────────────────────────────

def compute_match_score(resume: ParsedResume, job: Job) -> float:
    """Return a match score 0–100 for a (resume, job) pair."""
    job_skills_raw = job.skills if isinstance(job.skills, str) else "[]"
    try:
        raw_parsed = json.loads(job_skills_raw)
        job_skills: list = raw_parsed if isinstance(raw_parsed, list) else []
    except Exception:
        job_skills = []

    semantic = _semantic_score(resume.raw_text, job.description)
    skill    = _skill_overlap_score(resume.skills, job_skills)
    seniority = _seniority_score(resume.seniority_level, job.seniority_level)
    keyword  = _keyword_density_score(resume.raw_text, job.description)

    raw = (
        W_SEMANTIC  * semantic +
        W_SKILL     * skill +
        W_SENIORITY * seniority +
        W_KEYWORD   * keyword
    )
    return round(min(100.0, raw * 100), 1)


async def score_jobs_for_resume(
    resume: ParsedResume,
    jobs: list[Job],
) -> list[Job]:
    """
    Compute match scores for all jobs, attach to job objects in-place,
    and return sorted by descending score.
    """
    import asyncio

    # Embed resume once; run scoring in thread pool to avoid blocking
    loop = asyncio.get_event_loop()

    def _score_all():
        for job in jobs:
            job.match_score = compute_match_score(resume, job)
        return sorted(jobs, key=lambda j: j.match_score or 0, reverse=True)

    return await loop.run_in_executor(None, _score_all)
