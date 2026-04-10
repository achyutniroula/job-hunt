"""
ATS resume optimizer powered by Claude.

Pipeline:
  1. Clean, clarify, and keyword-align the resume (no reframing or title reinterpretation)
  2. Structured change output with categories
  3. ATS keyword scoring (before/after)
  4. LaTeX generation from Overleaf template
  5. Re-optimization loop support
"""
from __future__ import annotations

import asyncio
import logging
import os
import re

import anthropic

from app.core.config import get_settings
from app.schemas.resume import ATSOptimizeResponse, ChangeItem
from app.services.github_ingestion import GitHubProfile
from app.services.linkedin_ingestion import LinkedInProfile
from app.services.skill_inference import UserSkillProfile

logger = logging.getLogger(__name__)
settings = get_settings()

# ── XML tag parser ────────────────────────────────────────────────────────────

def _extract_tag(text: str, tag: str) -> str:
    m = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
    return m.group(1).strip() if m else ""


# ── System prompt ─────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are a precise ATS resume editor. Your job is to clean, clarify, and subtly \
keyword-align the candidate's resume — nothing more.

STRICT RULES:
1. PRESERVE EVERYTHING AS-IS: Keep all job titles, company names, dates, section order, \
   URLs, and factual content exactly as written. Do NOT rename jobs, reinterpret \
   responsibilities, reframe narratives, or infer roles the user didn't claim.
2. PRESERVE ALL URLS: Copy every LinkedIn, GitHub, portfolio, or other URL verbatim. \
   Never alter, shorten, or omit them.
3. NO NEW DASHES: Never introduce em-dashes (—), en-dashes (–), or hyphens that were \
   not already present in the original resume. Only retain dashes the user wrote.
4. ONE PAGE MAXIMUM: The entire optimized resume must fit on a single printed page. \
   Keep bullets concise (one line preferred, two lines absolute maximum). \
   If content is too long, tighten wording — never remove sections.
5. KEYWORD ALIGNMENT (minimal): If a required keyword from the job description \
   naturally fits into an existing bullet without forcing it, incorporate it. \
   Do not overuse keywords, do not add keyword-stuffed phrases, do not restructure \
   bullets around keywords.
6. VERB IMPROVEMENT: Replace weak verbs (worked on, helped, assisted) with stronger \
   past-tense action verbs only when the meaning is identical.
7. CLARITY: Fix grammar, redundancy, and vague wording. Tighten every bullet to its \
   clearest, most concise form.
8. NO FABRICATION: Do not invent metrics, achievements, skills, or any content not \
   present in the original.

OUTPUT FORMAT:
Output the cleaned resume, then:
---CHANGES---
List only actual changes made, one per line:
[VERB] what changed
[KEYWORD] what was added and where
[SKILL] skill clarified or lightly adjusted
[METRIC] metric preserved or clarified
[REMOVED] redundant/vague phrase removed
[RESTRUCTURE] minor structural fix

Then:
---IMPROVEMENTS---
2-3 concrete suggestions for the next pass only.
"""

_USER_TEMPLATE = """\
JOB DESCRIPTION:
{job_description}

RESUME:
{resume_text}

Apply all rules. Output the cleaned resume, then changes, then improvement suggestions.
"""

_REOPTIMIZE_USER_TEMPLATE = """\
JOB DESCRIPTION:
{job_description}

RESUME (pass {pass_num} — already partially optimized):
{resume_text}

APPLY THESE IMPROVEMENTS FROM LAST PASS:
{improvements}

Apply improvements while following all original rules. Output the full resume, then changes, \
then 2-3 new improvement suggestions.
"""

# ── LaTeX generation ──────────────────────────────────────────────────────────

_LATEX_SYSTEM = """\
You are a LaTeX resume formatter. Replace ONLY textual content in the template with the \
provided resume content. The result MUST fit on one page.

RULES:
- Never change LaTeX commands, packages, \\newcommand definitions, or formatting directives.
- Never add, remove, or rename sections.
- Never change \\resumeSubheading, \\resumeItem, \\resumeProjectHeading argument structure.
- Escape special characters: & → \\&, % → \\%, $ → \\$, # → \\#, _ → \\_
- URLs: output each URL as plain text exactly as given. Do NOT wrap in \\href, \\myuline, or any macro.
- ONE PAGE: if content is too long, trim bullet text (not sections) until it fits one page.
- Output ONLY the complete LaTeX document — no markdown, no explanation, no code fences.
"""

_LATEX_USER = """\
TEMPLATE:
{template}

RESUME CONTENT:
{optimized_text}

Inject the resume content into the template. Output must fit one page.
"""

# ── ATS scoring ───────────────────────────────────────────────────────────────

_STOPWORDS = {
    "with", "that", "this", "have", "from", "will", "your", "their", "they",
    "also", "must", "able", "work", "team", "role", "company", "position",
    "experience", "skills", "years", "knowledge", "strong", "ability",
    "excellent", "good", "great", "candidate", "looking", "required",
    "preferred", "including", "using", "about", "what", "where", "when",
    "working", "like", "join", "help", "make", "need", "some", "other",
    "provide", "ensure", "drive", "build", "develop", "support",
}


def _jd_keywords(job_description: str) -> set[str]:
    words = re.findall(r"\b[a-zA-Z][a-zA-Z+#.]{3,}\b", job_description.lower())
    return {w for w in words if w not in _STOPWORDS}


def _estimate_ats_score(resume_text: str, job_description: str) -> int:
    if not job_description:
        return 50
    keywords = _jd_keywords(job_description)
    if not keywords:
        return 50
    res_lower = resume_text.lower()
    hits = sum(1 for kw in keywords if kw in res_lower)
    # Scale: 100% overlap → ~85 (realistic ceiling), weighted by TF-IDF-like importance
    score = min(100, int((hits / len(keywords)) * 140))
    return max(5, score)


def _keyword_breakdown(
    optimized_text: str, job_description: str
) -> tuple[list[str], list[str]]:
    if not job_description:
        return [], []
    keywords = _jd_keywords(job_description)
    opt_lower = optimized_text.lower()
    matched = sorted(kw for kw in keywords if kw in opt_lower)[:25]
    missing = sorted(kw for kw in keywords if kw not in opt_lower)[:25]
    return matched, missing


# ── Change parsing ────────────────────────────────────────────────────────────

_CATEGORY_MAP = {
    "VERB": "verb",
    "KEYWORD": "keyword",
    "TITLE": "title",
    "SKILL": "skill",
    "METRIC": "metric",
    "REFRAME": "reframe",
    "REMOVED": "removed",
    "RESTRUCTURE": "restructure",
}

_CHANGE_RE = re.compile(r"^\[(VERB|KEYWORD|TITLE|SKILL|METRIC|REFRAME|REMOVED|RESTRUCTURE)\]\s*(.+)$")


def _parse_changes(raw: str) -> tuple[list[ChangeItem], list[str]]:
    """Parse structured [CATEGORY] lines into ChangeItem list + plain summary."""
    items: list[ChangeItem] = []
    plain: list[str] = []
    for line in raw.splitlines():
        line = line.strip().lstrip("•-*").strip()
        if not line:
            continue
        m = _CHANGE_RE.match(line)
        if m:
            cat = _CATEGORY_MAP.get(m.group(1), "reframe")
            text = m.group(2).strip()
            items.append(ChangeItem(category=cat, text=text))
            plain.append(text)
        else:
            plain.append(line)
    return items, plain


# ── LaTeX ─────────────────────────────────────────────────────────────────────

async def _generate_latex(optimized_text: str, client: anthropic.AsyncAnthropic) -> str | None:
    try:
        template_path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "../../../Resumes/source.txt")
        )
        if not os.path.exists(template_path):
            logger.warning("LaTeX template not found at %s", template_path)
            return None
        with open(template_path, encoding="utf-8") as f:
            template = f.read()

        msg = await client.messages.create(
            model=settings.anthropic_model,
            max_tokens=3000,
            system=_LATEX_SYSTEM,
            messages=[{
                "role": "user",
                "content": _LATEX_USER.format(
                    template=template,
                    optimized_text=optimized_text[:4000],
                ),
            }],
        )
        raw = msg.content[0].text.strip() if msg.content else ""
        # Strip any accidental markdown fences
        raw = re.sub(r"^```[a-z]*\n?", "", raw).rstrip("`").strip()
        return raw or None
    except Exception as exc:
        logger.warning("LaTeX generation failed: %s", exc)
        return None


# ── Public API ────────────────────────────────────────────────────────────────

async def optimize_resume(
    resume_text: str,
    job_description: str,
    previous_improvements: list[str] | None = None,
    pass_num: int = 1,
) -> ATSOptimizeResponse:
    """
    Optimize a resume against a job description.
    - pass_num > 1 → re-optimization mode (apply previous improvements).
    - Runs LaTeX generation concurrently.
    """
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    if pass_num > 1 and previous_improvements:
        user_message = _REOPTIMIZE_USER_TEMPLATE.format(
            job_description=job_description[:2000],
            resume_text=resume_text[:4000],
            improvements="\n".join(f"- {i}" for i in previous_improvements),
            pass_num=pass_num,
        )
    else:
        user_message = _USER_TEMPLATE.format(
            job_description=job_description[:2000],
            resume_text=resume_text[:4000],
        )

    try:
        message = await client.messages.create(
            model=settings.anthropic_model,
            max_tokens=2048,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
    except anthropic.APIError as exc:
        logger.error("Anthropic API error: %s", exc)
        raise

    full_response = message.content[0].text if message.content else ""

    # ── Parse improvements ───────────────────────────────────────────────────
    improvements: list[str] = []
    if "---IMPROVEMENTS---" in full_response:
        full_response, imp_raw = full_response.split("---IMPROVEMENTS---", 1)
        for line in imp_raw.splitlines():
            line = line.strip().lstrip("•-*123456789. ").strip()
            if line and len(line) > 10:
                improvements.append(line)

    # ── Parse changes + optimized text ──────────────────────────────────────
    if "---CHANGES---" in full_response:
        parts = full_response.split("---CHANGES---", 1)
        optimized_text = parts[0].strip()
        changes_raw = parts[1].strip()
    else:
        optimized_text = full_response.strip()
        changes_raw = ""

    change_items, changes_plain = _parse_changes(changes_raw)

    # ── Scoring ──────────────────────────────────────────────────────────────
    score_before = _estimate_ats_score(resume_text, job_description)
    score_after = _estimate_ats_score(optimized_text, job_description)
    matched, missing = _keyword_breakdown(optimized_text, job_description)

    # ── LaTeX (concurrent, best-effort) ─────────────────────────────────────
    latex_text = await _generate_latex(optimized_text, client)

    return ATSOptimizeResponse(
        original_text=resume_text,
        optimized_text=optimized_text,
        latex_text=latex_text,
        changes_summary=changes_plain,
        change_items=change_items,
        ats_score_before=score_before,
        ats_score_after=score_after,
        matched_keywords=matched,
        missing_keywords=missing,
        improvements=improvements,
    )


# ── Profile-aware optimization ────────────────────────────────────────────────

_PROFILE_SYSTEM = """\
You are an expert resume writer and ATS specialist. Complete all tasks below in one response \
using these exact XML tags. Be concise. No em dashes. No buzzwords: spearheaded, leveraged, \
utilized, streamlined, robust, scalable, cutting-edge, best practices, passionate about, \
results-driven. Sound like a smart human wrote it. Quantify only where the evidence supports \
a real number. One page maximum.
"""

_PROFILE_USER = """\
<job_analysis>
Extract from the job description: required skills, preferred skills, ATS keywords that must \
appear verbatim, seniority signals.
</job_analysis>

<gap_analysis>
Compare job requirements against:
CONFIRMED SKILLS: {confirmed_skills}
INFERRED SKILLS: {inferred_skills}
PROJECT EVIDENCE: {project_evidence}
SENIORITY SIGNALS: {seniority_signals}

List: skills user clearly has (with evidence), skills inferable from project work, honest gaps \
(skills job wants that user does not demonstrably have).
</gap_analysis>

<optimized_resume>
Rewrite the resume against the job description. Weave in ATS keywords naturally. Use project \
evidence to support skill claims. Reframe existing descriptions using stronger technical language \
about what they actually built. For adjacent skills (e.g. user used REST, job wants GraphQL), \
highlight transferable depth — do not fabricate. Every claim must trace to real evidence. \
No em dashes. No parallel bullet fatigue. Vary sentence structure. One page max.

RESUME:
{resume_text}
</optimized_resume>

<transparency_report>
List every change made: what was reworded and why (cite evidence), what keywords were added and \
where, what was inferred from GitHub vs explicitly stated, honest gap list with study suggestions, \
what the user should be ready to discuss in interview.
</transparency_report>

<interview_prep>
For every skill prominently featured (especially inferred or reframed ones): one likely interview \
question + a one-sentence honest answer framework based on actual project evidence.
</interview_prep>

JOB DESCRIPTION:
{job_description}

GITHUB PROJECTS:
{github_summary}
"""


async def optimize_with_profile(
    resume_text: str,
    job_description: str,
    skill_profile: UserSkillProfile,
    github_profile: GitHubProfile | None = None,
    linkedin_profile: LinkedInProfile | None = None,
) -> ATSOptimizeResponse:
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    # Build github summary
    github_summary = ""
    if github_profile:
        lines = [f"Username: {github_profile.username}",
                 f"Top languages: {', '.join(list(github_profile.top_languages.keys())[:8])}"]
        for r in github_profile.repos[:6]:
            lang_str = ", ".join(list(r.languages.keys())[:4])
            lines.append(f"- {r.name}: {r.description or ''} [{lang_str}] topics={r.topics}")
            if r.readme_excerpt:
                lines.append(f"  README: {r.readme_excerpt[:300]}")
        github_summary = "\n".join(lines)

    user_msg = _PROFILE_USER.format(
        confirmed_skills=", ".join(skill_profile.confirmed_skills[:30]),
        inferred_skills=", ".join(skill_profile.inferred_skills[:20]),
        project_evidence=str(dict(list(skill_profile.project_evidence.items())[:15])),
        seniority_signals="; ".join(skill_profile.seniority_signals),
        resume_text=resume_text[:4000],
        job_description=job_description[:2000],
        github_summary=github_summary[:2000],
    )

    try:
        message = await client.messages.create(
            model=settings.anthropic_model,
            max_tokens=3500,
            system=_PROFILE_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
        )
    except anthropic.APIError as exc:
        logger.error("Anthropic API error (profile optimize): %s", exc)
        raise

    full = message.content[0].text if message.content else ""

    optimized_text = _extract_tag(full, "optimized_resume") or resume_text
    transparency = _extract_tag(full, "transparency_report")
    interview = _extract_tag(full, "interview_prep")
    gap = _extract_tag(full, "gap_analysis")

    score_before = _estimate_ats_score(resume_text, job_description)
    score_after = _estimate_ats_score(optimized_text, job_description)
    matched, missing = _keyword_breakdown(optimized_text, job_description)

    latex_text = await _generate_latex(optimized_text, client)

    linkedin_unavailable = linkedin_profile.linkedin_unavailable if linkedin_profile else False

    return ATSOptimizeResponse(
        original_text=resume_text,
        optimized_text=optimized_text,
        latex_text=latex_text,
        changes_summary=[],
        change_items=[],
        ats_score_before=score_before,
        ats_score_after=score_after,
        matched_keywords=matched,
        missing_keywords=missing,
        improvements=[],
        transparency_report=transparency,
        interview_prep=interview,
        gap_analysis=gap,
        linkedin_unavailable=linkedin_unavailable,
    )
