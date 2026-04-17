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
import json
import logging
import os
import re

import anthropic

from app.core.config import get_settings
from app.schemas.resume import ATSOptimizeResponse, ChangeItem
from app.services.github_ingestion import GitHubDigest, GitHubProfile
from app.services.linkedin_ingestion import LinkedInProfile
from app.services.skill_inference import UserSkillProfile

logger = logging.getLogger(__name__)
settings = get_settings()

# ── XML tag parser ────────────────────────────────────────────────────────────

def _extract_tag(text: str, tag: str) -> str:
    m = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
    return m.group(1).strip() if m else ""


def _parse_role_reframes(text: str) -> list[dict]:
    entries = []
    for block in re.split(r"-{3,}", text):
        orig = re.search(r"ORIGINAL:\s*(.+)", block)
        new  = re.search(r"NEW:\s*(.+)", block)
        why  = re.search(r"WHY:\s*(.+)", block)
        if orig and new and why:
            entries.append({
                "original": orig.group(1).strip(),
                "reframed": new.group(1).strip(),
                "justification": why.group(1).strip(),
            })
    return entries


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
You are a LaTeX resume formatter. Inject the provided resume content into the template.

STRICT RULES:
- Font size is 11pt throughout — never change it.
- ONE PAGE HARD LIMIT: the compiled PDF must fit exactly one page. Trim bullet text (never sections) until it fits.
- Never change LaTeX commands, packages, \\newcommand definitions, or formatting directives.
- The PROJECTS section MUST contain exactly 5 \\resumeProjectHeading entries. Copy the template's \\resumeProjectHeading structure and add entries as needed.
- Never change \\resumeSubheading, \\resumeItem, \\resumeProjectHeading argument structure.
- Escape special characters: & → \\&, % → \\%, $ → \\$, # → \\#, _ → \\_
- URLs in the heading: preserve the \\href{...}{\\myuline{...}} pattern exactly. Do not convert to plain text.
- Output ONLY the complete LaTeX document — no markdown, no explanation, no code fences.
"""

_LATEX_USER = """\
TEMPLATE:
{template}

RESUME CONTENT:
{optimized_text}

Inject content into template. PROJECTS section must have exactly 5 entries. Must fit one page at 11pt.
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
            max_tokens=4000,
            system=_LATEX_SYSTEM,
            messages=[{
                "role": "user",
                "content": (
                    _LATEX_USER
                    .replace("{template}", template)
                    .replace("{optimized_text}", optimized_text[:4000])
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
        user_message = (
            _REOPTIMIZE_USER_TEMPLATE
            .replace("{job_description}", job_description[:2000])
            .replace("{resume_text}", resume_text[:4000])
            .replace("{improvements}", "\n".join(f"- {i}" for i in previous_improvements))
            .replace("{pass_num}", str(pass_num))
        )
    else:
        user_message = (
            _USER_TEMPLATE
            .replace("{job_description}", job_description[:2000])
            .replace("{resume_text}", resume_text[:4000])
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

<role_reframing>
Review each position title on the resume against its bullet points. For any role where the \
described work clearly maps to a more precise, function-based title, output:
ORIGINAL: <current title>
NEW: <accurate title based on actual work>
WHY: <one sentence citing the work described>
---
Only rename where truthfully supported by the bullet content. Leave accurate titles unchanged. \
Do not inflate seniority. If no rename is warranted, output nothing.
</role_reframing>

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

    user_msg = (
        _PROFILE_USER
        .replace("{confirmed_skills}", ", ".join(skill_profile.confirmed_skills[:30]))
        .replace("{inferred_skills}", ", ".join(skill_profile.inferred_skills[:20]))
        .replace("{project_evidence}", str(dict(list(skill_profile.project_evidence.items())[:15])))
        .replace("{seniority_signals}", "; ".join(skill_profile.seniority_signals))
        .replace("{resume_text}", resume_text[:4000])
        .replace("{job_description}", job_description[:2000])
        .replace("{github_summary}", github_summary[:2000])
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
    role_reframes = _parse_role_reframes(_extract_tag(full, "role_reframing"))
    if role_reframes:
        transparency += "\n\nRole Titles Reframed:\n" + "\n".join(
            f"- {r['original']} → {r['reframed']}: {r['justification']}"
            for r in role_reframes
        )

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
        role_reframes=role_reframes,
    )


# ── Session-based optimization (uses pre-fetched GitHub context) ──────────────

_SESSION_OPT_USER = """\
<job_analysis>
Extract from the job description: required skills, preferred skills, ATS keywords, seniority signals.
</job_analysis>

<gap_analysis>
Compare job requirements against resume and GitHub evidence.
List: confirmed skills (with evidence), inferrable skills from GitHub code, honest gaps.
</gap_analysis>

<optimized_resume>
Produce a complete rewritten resume following ALL rules below:

PROJECTS SECTION — MANDATORY:
- Select exactly 5 DISTINCT GitHub repositories from the GitHub data below.
- Use the EXACT repository name as it appears in the GitHub data (e.g. "[repo-name]") — never rename, paraphrase, or invent variants.
- Each entry must reference a different repo name. If two entries would share the same name, replace one with a different repo.
- Do NOT include repos already mentioned under Experience.
- For each project write exactly 2 concise bullet points (≤12 words each) highlighting JD-relevant technical aspects.
- Format each project as:  <Exact Repo Name> | <comma-separated tech stack>
- Output all 5. Never duplicate a repo name.

EXPERIENCE SECTION:
- You MAY rename a role title if the actual described work more precisely matches a different function-based title.
- Trim each bullet to ≤15 words. Remove filler. Prioritize JD-keyword alignment.
- Keep only the 2–3 strongest bullets per role if space is tight.

GENERAL RULES:
- ONE PAGE, 11pt font throughout. If content is too long, compact bullets — never remove sections.
- Weave in ATS keywords naturally. No em dashes. No buzzwords.
- Preserve all URLs, dates, company names, and factual content exactly.

RESUME:
{resume_text}
</optimized_resume>

<transparency_report>
Every change: rewording reason (cite GitHub evidence), keywords added, roles renamed and why, projects selected and why.
</transparency_report>

<interview_prep>
For each of the 5 projects and any reframed role: one likely interview question + one-sentence honest answer framework.
</interview_prep>

<role_reframing>
For each renamed role:
ORIGINAL: <current title>
NEW: <new title>
WHY: <one sentence citing the work>
---
Only include renamed roles. Output nothing if none.
</role_reframing>

JOB DESCRIPTION:
{job_description}

GITHUB PROJECTS (deep context — file tree, key files, README):
{github_summary}
"""


def _build_rich_github_summary(github_context_json: str) -> str:
    try:
        data = json.loads(github_context_json)
    except Exception:
        return ""

    langs = ", ".join(list((data.get("top_languages") or {}).keys())[:8])
    lines = [f"GitHub: @{data.get('username')} | Top languages: {langs}"]

    seen: set[str] = set()
    for r in (data.get("repos") or []):
        if r["name"] in seen:
            continue
        seen.add(r["name"])
        repo_langs = ", ".join(list((r.get("languages") or {}).keys())[:5])
        topics = ", ".join((r.get("topics") or [])[:5])
        lines.append(f"\n[{r['name']}] {r.get('description') or ''}")
        if repo_langs:
            lines.append(f"  Languages: {repo_langs}")
        if topics:
            lines.append(f"  Topics: {topics}")
        tree = r.get("file_tree") or []
        if tree:
            lines.append(f"  Files ({len(tree)}): {' '.join(tree[:30])}")
        readme = r.get("readme") or r.get("readme_excerpt")
        if readme:
            lines.append(f"  README: {readme[:500]}")
        for path, content in list((r.get("key_files") or {}).items())[:3]:
            lines.append(f"  [{path}]: {content[:300]}")

    return "\n".join(lines)


async def optimize_for_session(
    resume_text: str,
    job_description: str,
    github_context_json: str | None = None,
) -> ATSOptimizeResponse:
    """Optimize using pre-fetched deep GitHub context stored in an interview session."""
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    github_summary = _build_rich_github_summary(github_context_json) if github_context_json else "No GitHub data."

    user_msg = (
        _SESSION_OPT_USER
        .replace("{job_description}", job_description[:2000])
        .replace("{github_summary}", github_summary[:5000])
        .replace("{resume_text}", resume_text[:4000])
    )

    try:
        message = await client.messages.create(
            model=settings.anthropic_model,
            max_tokens=4500,
            system=_PROFILE_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
        )
    except anthropic.APIError as exc:
        logger.error("Anthropic API error (session optimize): %s", exc)
        raise

    full = message.content[0].text if message.content else ""

    optimized_text = _extract_tag(full, "optimized_resume") or resume_text
    transparency = _extract_tag(full, "transparency_report")
    interview = _extract_tag(full, "interview_prep")
    gap = _extract_tag(full, "gap_analysis")
    role_reframes = _parse_role_reframes(_extract_tag(full, "role_reframing"))
    if role_reframes:
        transparency += "\n\nRole Titles Reframed:\n" + "\n".join(
            f"- {r['original']} → {r['reframed']}: {r['justification']}"
            for r in role_reframes
        )

    score_before = _estimate_ats_score(resume_text, job_description)
    score_after = _estimate_ats_score(optimized_text, job_description)
    matched, missing = _keyword_breakdown(optimized_text, job_description)

    latex_text = await _generate_latex(optimized_text, client)

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
        linkedin_unavailable=False,
        role_reframes=role_reframes,
    )


# ── Single-call digest optimizer ──────────────────────────────────────────────

_DIGEST_SYSTEM = """\
You are a world-class technical resume writer and ATS optimization specialist.

You have been given three inputs:
  1. The candidate's current resume
  2. A target job description
  3. The candidate's complete GitHub profile — every public repo they own, including
     READMEs, full file trees, dependency files, CI/CD configs, and source code

YOUR MISSION:
Produce the single highest ATS score this candidate can legitimately achieve for this
specific job, using only what is truthfully evidenced by their resume and GitHub repos.

CORE PRINCIPLES:
- Never fabricate. Every claim must trace to the resume text or a specific named GitHub
  repo and file. If you cite a technology, name the repo it came from.
- GitHub is ground truth. If a repo proves the candidate built something relevant that
  they never mentioned on their resume, surface it — it is real experience they forgot
  to claim. Name the repo explicitly.
- Exact JD keywords beat synonyms. ATS systems do literal string matching. If the JD
  says "distributed systems", use that exact phrase, not "scalable architecture".
- Quantify with evidence. Use GitHub signals: stars, forks, number of files, dependency
  count, CI/CD presence. Infer conservatively — a 200-file repo with CI/CD implies
  production-grade work. Never invent numbers.
- XYZ bullet format: "Accomplished [X] as measured by [Y], by doing [Z]."
- One page. Bullets <= 15 words. If content is too long, tighten wording — never
  remove sections. No em dashes. No buzzwords: spearheaded, leveraged, utilized,
  streamlined, robust, cutting-edge, passionate about, results-driven.
- ATS score is your calibrated expert estimate of how a real ATS parses this resume
  against this JD. A resume with near-complete keyword coverage and strong formatting
  scores 88-93. Do not inflate. Do not deflate.
"""

_DIGEST_USER = """\
<resume>
{resume_text}
</resume>

<job_description>
{job_description}
</job_description>

<github_profile>
{github_context}
</github_profile>

Analyze all three inputs thoroughly. Then produce your output in this exact structure:

<optimized_resume>
Complete rewritten resume as plain text, ready to copy.
Must include: summary, experience (with rewritten bullets), skills, projects (exactly 5,
drawn from GitHub repos most relevant to this JD — use exact repo names).
</optimized_resume>

<ats_score_before>
[single integer 0-100: your calibrated estimate of the ORIGINAL resume's ATS score against this JD]
</ats_score_before>

<ats_score_after>
[single integer 0-100: your calibrated estimate of the OPTIMIZED resume's ATS score]
</ats_score_after>

<matched_keywords>
[comma-separated: every JD keyword or phrase present in the optimized resume]
</matched_keywords>

<missing_keywords>
[comma-separated: JD keywords the candidate cannot honestly claim — genuine gaps only]
</missing_keywords>

<transparency_report>
For every change made: what changed, why, and the exact source (resume or github:repo-name/file).
Call out explicitly: which GitHub repos surfaced skills not on the original resume,
which repo names were used in the projects section and why, which JD keywords were
injected and where. Be specific — vague entries like "improved bullet" are not acceptable.
</transparency_report>

<gap_analysis>
Skills and experience the JD requires that are absent from both the resume and all GitHub
repos. Be honest. Do not soften genuine gaps. For each gap suggest one concrete way to
address it (course, project idea, certification).
</gap_analysis>

<interview_prep>
For every skill prominently featured — especially any surfaced from GitHub that was not
on the original resume: one realistic interview question the candidate will face + a
one-sentence honest answer framework grounded in their actual GitHub evidence.
</interview_prep>

<role_reframing>
For each job title on the resume where the actual described work maps more precisely to a
different function-based title:
ORIGINAL: <current title>
NEW: <more accurate title based on the bullets and GitHub work>
WHY: <one sentence citing specific evidence>
---
Only include renamed roles. Output nothing here if no renames are warranted.
Do not inflate seniority.
</role_reframing>

---CHANGES---
One line per change. Format: [TYPE] description | source: resume or github:repo-name
TYPE must be one of: ROLE | BULLET | SKILL | PROJECT | KEYWORD
"""


async def optimize_with_digest(
    resume_text: str,
    job_description: str,
    github_digest: "GitHubDigest | None" = None,
) -> ATSOptimizeResponse:
    """
    Full-depth ATS optimizer. Claude receives the complete resume, complete JD,
    and complete GitHub context serialized from GitHubDigest.to_context_string().
    No pre-filtering. No Python-side scoring. One Claude call.
    """
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    github_context = (
        github_digest.to_context_string()
        if github_digest is not None
        else "No GitHub data provided."
    )

    user_msg = (
        _DIGEST_USER
        .replace("{resume_text}", resume_text)
        .replace("{job_description}", job_description)
        .replace("{github_context}", github_context)
    )

    try:
        message = await client.messages.create(
            model=settings.anthropic_model,
            max_tokens=6000,
            system=_DIGEST_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
        )
    except anthropic.APIError as exc:
        logger.error("Anthropic API error (digest optimize): %s", exc)
        raise

    full = message.content[0].text if message.content else ""

    optimized_text = _extract_tag(full, "optimized_resume") or resume_text

    def _safe_int(tag: str, fallback: int) -> int:
        raw = _extract_tag(full, tag).strip()
        try:
            return max(0, min(100, int(raw)))
        except (ValueError, TypeError):
            return fallback

    score_before = _safe_int("ats_score_before", 0)
    score_after  = _safe_int("ats_score_after", 0)

    def _csv_tag(tag: str) -> list[str]:
        raw = _extract_tag(full, tag)
        if not raw:
            return []
        return [k.strip() for k in raw.split(",") if k.strip()][:40]

    matched  = _csv_tag("matched_keywords")
    missing  = _csv_tag("missing_keywords")

    transparency  = _extract_tag(full, "transparency_report")
    gap           = _extract_tag(full, "gap_analysis")
    interview     = _extract_tag(full, "interview_prep")
    role_reframes = _parse_role_reframes(_extract_tag(full, "role_reframing"))

    if role_reframes:
        transparency += "\n\nRole Titles Reframed:\n" + "\n".join(
            f"- {r['original']} -> {r['reframed']}: {r['justification']}"
            for r in role_reframes
        )

    changes_raw = ""
    if "---CHANGES---" in full:
        changes_raw = full.split("---CHANGES---", 1)[1].strip()
    change_items, changes_plain = _parse_changes(changes_raw)

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
        improvements=[],
        transparency_report=transparency,
        interview_prep=interview,
        gap_analysis=gap,
        linkedin_unavailable=False,
        role_reframes=role_reframes,
    )
