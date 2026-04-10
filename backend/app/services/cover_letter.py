"""
Human-tone cover letter generator powered by Claude.

Produces concise, conversational, non-robotic cover letters
that sound like the candidate actually wrote them.
"""
from __future__ import annotations

import logging

import anthropic

from app.core.config import get_settings
from app.schemas.resume import CoverLetterResponse

logger = logging.getLogger(__name__)
settings = get_settings()

_SYSTEM_PROMPT = """\
You are a professional career coach who helps people write authentic, \
compelling cover letters that actually get read.

Your writing style:
- Conversational and direct — like a confident human talking, not a corporate drone
- Short sentences. No jargon. No fluff.
- Confident but never arrogant
- Specific and concrete — use real details from the resume
- Never use these phrases: "I am writing to express my interest", \
"I believe I would be a great fit", "Please find attached", \
"I look forward to hearing from you at your earliest convenience", \
"synergy", "leverage", "passionate about", "dynamic team"
- Opening hook that grabs attention immediately
- Three to four short paragraphs maximum
- Closing with a clear, simple call to action

STRICT RULES:
1. Only mention experience and skills that are in the provided resume.
2. Never fabricate achievements, companies, or credentials.
3. Tailor specifically to the job and company — do NOT write a generic letter.
4. Total length: 200-300 words. No more.
"""

_USER_TEMPLATE = """\
## Candidate Resume:
{resume_text}

## Job Details:
- Title: {job_title}
- Company: {company_name}
- Job Description:
{job_description}

{extra_notes}

Write a cover letter for this candidate applying to this role. \
Make it sound genuinely human — like they sat down and wrote it themselves. \
Keep it under 300 words.
"""


async def generate_cover_letter(
    resume_text: str,
    job_title: str,
    company_name: str,
    job_description: str,
    extra_notes: str | None = None,
) -> CoverLetterResponse:
    """
    Generate a human-sounding cover letter via Claude.
    """
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    notes_section = (
        f"## Extra context from candidate:\n{extra_notes}"
        if extra_notes
        else ""
    )

    user_message = _USER_TEMPLATE.format(
        resume_text=resume_text[:4000],
        job_title=job_title or "the role",
        company_name=company_name or "your company",
        job_description=job_description[:2000] if job_description else "Not provided",
        extra_notes=notes_section,
    )

    try:
        message = await client.messages.create(
            model=settings.anthropic_model,
            max_tokens=1024,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
    except anthropic.APIError as exc:
        logger.error("Anthropic API error during cover letter generation: %s", exc)
        raise

    cover_letter = message.content[0].text.strip() if message.content else ""
    word_count = len(cover_letter.split())

    return CoverLetterResponse(
        cover_letter=cover_letter,
        word_count=word_count,
    )
