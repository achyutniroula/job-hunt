"""Interview Q&A generator — uses Groq for speed, falls back to Anthropic."""
from __future__ import annotations

import json
import logging
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.interview import InterviewQA, InterviewSession

logger = logging.getLogger(__name__)

_PROMPT_TEMPLATE = """\
Generate interview questions and strong answers for this candidate.

JOB: {job_title} at {company_name}
JOB DESCRIPTION: {jd}
CANDIDATE RESUME: {resume}

Return a JSON array only. No preamble, no markdown fences. Schema:
[
  {{
    "category": "technical|behavioral|situational|role-specific",
    "question": "...",
    "answer": "..."
  }}
]

Generate exactly: 5 technical, 4 behavioral, 3 situational, 3 role-specific questions.
Answers must reference the candidate's actual experience. Be specific, not generic."""


async def _call_groq(prompt: str) -> str:
    import httpx
    settings = get_settings()
    if not settings.groq_api_key:
        raise RuntimeError("No GROQ_API_KEY")

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 3000,
                "temperature": 0.5,
            },
            headers={
                "Authorization": f"Bearer {settings.groq_api_key}",
                "Content-Type": "application/json",
            },
        )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


async def _call_anthropic(prompt: str) -> str:
    import anthropic
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise RuntimeError("No ANTHROPIC_API_KEY")

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    msg = await client.messages.create(
        model=settings.anthropic_model,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()


async def generate_qa(session: InterviewSession, db: AsyncSession) -> list[InterviewQA]:
    # Return cached rows if they exist
    existing = (
        await db.execute(
            select(InterviewQA)
            .where(InterviewQA.session_id == session.id)
            .order_by(InterviewQA.order_index)
        )
    ).scalars().all()
    if existing:
        return list(existing)

    prompt = _PROMPT_TEMPLATE.format(
        job_title=session.job_title,
        company_name=session.company_name,
        jd=(session.job_description or "")[:1000],
        resume=(session.resume_text or "")[:800],
    )

    raw = ""
    try:
        raw = await _call_groq(prompt)
        logger.info("QA generated via Groq for session %s", session.id)
    except Exception as groq_err:
        logger.warning("Groq QA failed (%s), trying Anthropic", groq_err)
        try:
            raw = await _call_anthropic(prompt)
            logger.info("QA generated via Anthropic for session %s", session.id)
        except Exception as anthro_err:
            logger.error("Both QA providers failed: %s", anthro_err)
            return []

    # Extract JSON array
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        logger.error("No JSON array in QA response: %s", raw[:200])
        return []

    try:
        items = json.loads(match.group())
    except json.JSONDecodeError as e:
        logger.error("JSON parse error in QA response: %s", e)
        return []

    rows = [
        InterviewQA(
            session_id=session.id,
            category=item.get("category", "general"),
            question=item.get("question", ""),
            answer=item.get("answer", ""),
            order_index=idx,
        )
        for idx, item in enumerate(items)
        if item.get("question")
    ]

    if rows:
        db.add_all(rows)
        await db.commit()

    return rows
