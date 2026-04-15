"""Interview Prep API routes."""
from __future__ import annotations

import asyncio
import dataclasses
import json
import os
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, get_db
from app.models.interview import (
    BrainstormMessage,
    BrainstormThread,
    InterviewChatMessage,
    InterviewQA,
    InterviewSession,
)
from app.schemas.interview import (
    BrainstormMessageOut,
    BrainstormReply,
    BrainstormThreadCreate,
    BrainstormThreadOut,
    BrainstormThreadRename,
    ChatMessageIn,
    ChatMessageOut,
    ChatReply,
    InterviewQAOut,
    InterviewSessionCreate,
    InterviewSessionOut,
    InterviewSessionSummary,
    SessionResumeUpdate,
)
from app.services.company_enrichment import enrich_company
from app.services.github_ingestion import fetch_github_profile
from app.services.groq_chat import groq_chat

router = APIRouter()

_RESUME_DIR = os.environ.get("INTERVIEW_RESUME_DIR", "data/resumes")


def _resume_path(session_id: str) -> str:
    return os.path.join(_RESUME_DIR, f"{session_id}.pdf")


def _format_github_for_prompt(github_context: str) -> str:
    """Convert stored github JSON into a rich LLM-friendly string."""
    try:
        data = json.loads(github_context)
    except Exception:
        return ""

    langs = ", ".join(list((data.get("top_languages") or {}).keys())[:8])
    lines = [
        f"=== GITHUB PROFILE: @{data.get('username')} ===",
        f"Top languages across all repos: {langs}",
        f"Total public repos: {data.get('total_repos', 0)}",
        "",
    ]

    for r in (data.get("repos") or []):
        desc = r.get("description") or "(no description)"
        repo_langs = ", ".join(list((r.get("languages") or {}).keys())[:6])
        topics = ", ".join((r.get("topics") or [])[:6])
        lines.append(f"--- Repo: {r['name']} (stars:{r.get('stars',0)}) ---")
        lines.append(f"Description: {desc}")
        if repo_langs:
            lines.append(f"Languages: {repo_langs}")
        if topics:
            lines.append(f"Topics: {topics}")

        # File tree (show structure, truncated)
        tree = r.get("file_tree") or []
        if tree:
            lines.append(f"File structure ({len(tree)} files):")
            lines.append("  " + "  ".join(tree[:40]))

        # README
        readme = r.get("readme") or r.get("readme_excerpt")
        if readme:
            lines.append(f"README (excerpt):\n{readme[:1500]}")

        # Key files
        key_files = r.get("key_files") or {}
        for path, content in list(key_files.items())[:5]:
            lines.append(f"File: {path}\n{content[:1500]}")

        lines.append("")

    return "\n".join(lines)


def _make_pdf(session_id: str, resume_text: str) -> str:
    from fpdf import FPDF

    os.makedirs(_RESUME_DIR, exist_ok=True)
    path = _resume_path(session_id)

    pdf = FPDF()
    pdf.set_margins(20, 20, 20)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    pdf.set_auto_page_break(auto=True, margin=20)

    for line in resume_text.split("\n"):
        safe = line.encode("latin-1", errors="replace").decode("latin-1")
        if safe.strip():
            pdf.multi_cell(pdf.epw, 6, safe)
        else:
            pdf.ln(4)

    pdf.output(path)
    return path


async def _run_qa_background(session_id: str) -> None:
    from app.services.interview_qa_generator import generate_qa

    async with AsyncSessionLocal() as db:
        session = await db.get(InterviewSession, session_id)
        if session:
            await generate_qa(session, db)


# ── Session endpoints ─────────────────────────────────────────────────────────

@router.post("/session", response_model=InterviewSessionOut)
async def create_session(
    body: InterviewSessionCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    # Fetch company links and GitHub in parallel
    github_fetch = (
        fetch_github_profile(body.github_url) if body.github_url and body.github_url.strip() else None
    )
    if github_fetch:
        links, github_profile = await asyncio.gather(
            enrich_company(body.company_name),
            asyncio.wait_for(github_fetch, timeout=15),
            return_exceptions=True,
        )
        if isinstance(links, Exception):
            from app.services.company_enrichment import CompanyLinks
            links = CompanyLinks()
        if isinstance(github_profile, Exception):
            github_profile = None
    else:
        links = await enrich_company(body.company_name)
        github_profile = None

    github_context_str: str | None = None
    if github_profile:
        try:
            github_context_str = json.dumps(dataclasses.asdict(github_profile))
        except Exception:
            pass

    session = InterviewSession(
        id=str(uuid.uuid4()),
        job_title=body.job_title,
        job_description=body.job_description,
        company_name=body.company_name,
        resume_text=body.resume_text,
        github_url=body.github_url,
        github_context=github_context_str,
        salary_info=body.salary_info,
        location=body.location,
        seniority=body.seniority,
        company_website=links.website,
        company_careers_url=links.careers_url,
        company_glassdoor_url=links.glassdoor_url,
        company_linkedin_url=links.linkedin_url,
        company_indeed_url=links.indeed_url,
    )

    # Generate PDF if resume text provided
    if body.resume_text.strip():
        try:
            path = _make_pdf(session.id, body.resume_text)
            session.resume_pdf_path = path
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("PDF generation failed: %s", exc)

    db.add(session)
    await db.commit()
    await db.refresh(session)

    background_tasks.add_task(_run_qa_background, session.id)

    return InterviewSessionOut.model_validate(session)


@router.get("/session/{session_id}", response_model=InterviewSessionOut)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    session = await db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return InterviewSessionOut.model_validate(session)


@router.get("/sessions", response_model=list[InterviewSessionSummary])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(InterviewSession).order_by(InterviewSession.created_at.desc())
        )
    ).scalars().all()
    return [InterviewSessionSummary.model_validate(r) for r in rows]


@router.delete("/session/{session_id}")
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    session = await db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    # Clean up PDF
    path = _resume_path(session_id)
    if os.path.exists(path):
        os.remove(path)
    await db.delete(session)
    await db.commit()
    return {"deleted": session_id}


# ── Q&A ───────────────────────────────────────────────────────────────────────

@router.get("/session/{session_id}/qa", response_model=dict[str, list[InterviewQAOut]])
async def get_qa(session_id: str, db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(InterviewQA)
            .where(InterviewQA.session_id == session_id)
            .order_by(InterviewQA.order_index)
        )
    ).scalars().all()

    grouped: dict[str, list[InterviewQAOut]] = {}
    for row in rows:
        cat = row.category
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(InterviewQAOut.model_validate(row))
    return grouped


# ── Resume PDF ────────────────────────────────────────────────────────────────

@router.get("/session/{session_id}/resume.pdf")
async def get_resume_pdf(session_id: str, db: AsyncSession = Depends(get_db)):
    path = _resume_path(session_id)
    if not os.path.exists(path):
        # Try to regenerate from stored resume_text
        session = await db.get(InterviewSession, session_id)
        if not session:
            raise HTTPException(404, "Session not found")
        if not session.resume_text or not session.resume_text.strip():
            raise HTTPException(404, "PDF not available: no resume text stored")
        try:
            path = _make_pdf(session_id, session.resume_text)
            session.resume_pdf_path = path
            await db.commit()
        except Exception as exc:
            raise HTTPException(500, f"Failed to generate PDF: {exc}") from exc
    return FileResponse(path, media_type="application/pdf", filename=f"resume_{session_id}.pdf")


# ── GitHub data ──────────────────────────────────────────────────────────────

@router.get("/session/{session_id}/github")
async def get_github_data(session_id: str, db: AsyncSession = Depends(get_db)):
    session = await db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    if not session.github_context:
        raise HTTPException(404, "No GitHub data for this session")
    try:
        return json.loads(session.github_context)
    except Exception:
        raise HTTPException(500, "Failed to parse GitHub data")


@router.get("/session/{session_id}/github/{repo_name}/explain")
async def explain_repo(session_id: str, repo_name: str, db: AsyncSession = Depends(get_db)):
    session = await db.get(InterviewSession, session_id)
    if not session or not session.github_context:
        raise HTTPException(404, "No GitHub data for this session")

    try:
        data = json.loads(session.github_context)
    except Exception:
        raise HTTPException(500, "Failed to parse GitHub data")

    repo = next((r for r in data.get("repos", []) if r["name"] == repo_name), None)
    if not repo:
        raise HTTPException(404, f"Repo '{repo_name}' not found in session")

    langs = ", ".join(list((repo.get("languages") or {}).keys())[:6])
    topics = ", ".join((repo.get("topics") or [])[:6])
    readme = (repo.get("readme") or "")[:1500]
    key_files_text = "\n".join(
        f"[{path}]\n{content[:600]}"
        for path, content in list((repo.get("key_files") or {}).items())[:3]
    )
    tree_sample = "  ".join((repo.get("file_tree") or [])[:30])

    prompt = f"""You are reviewing a GitHub repository. Write a clear, concise project breakdown in this exact format:

**What it does:** 1-2 sentences on the purpose and main functionality.
**Tech stack:** List the key technologies, frameworks, and libraries used.
**Architecture:** 1-2 sentences on how the project is structured.
**Notable aspects:** Any interesting patterns, design decisions, or standout features.

Repository data:
Name: {repo["name"]}
Description: {repo.get("description") or "none"}
Languages: {langs}
Topics: {topics}
File structure: {tree_sample}
README: {readme}
Key files:
{key_files_text}

Be specific. Use only what the data shows."""

    explanation = await groq_chat(
        [{"role": "user", "content": prompt}],
        max_tokens=400,
    )
    return {"repo": repo_name, "explanation": explanation}


# ── Resume update + Session optimize ─────────────────────────────────────────

@router.patch("/session/{session_id}/resume", response_model=InterviewSessionOut)
async def update_resume(
    session_id: str,
    body: SessionResumeUpdate,
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    session.resume_text = body.resume_text
    try:
        path = _make_pdf(session_id, body.resume_text)
        session.resume_pdf_path = path
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("PDF regen failed: %s", exc)
    await db.commit()
    await db.refresh(session)
    return InterviewSessionOut.model_validate(session)


@router.get("/session/{session_id}/optimize")
async def get_optimize_result(session_id: str, db: AsyncSession = Depends(get_db)):
    session = await db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    if not session.optimize_result:
        raise HTTPException(404, "No optimization result saved yet")
    try:
        return json.loads(session.optimize_result)
    except Exception:
        raise HTTPException(500, "Failed to parse saved optimization result")


@router.post("/session/{session_id}/optimize")
async def optimize_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    from app.services.ats_optimizer import optimize_for_session
    session = await db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    if not session.resume_text or not session.resume_text.strip():
        raise HTTPException(400, "No resume text in this session")
    result = await optimize_for_session(
        resume_text=session.resume_text,
        job_description=session.job_description,
        github_context_json=session.github_context,
    )
    session.optimize_result = result.model_dump_json()
    await db.commit()
    return result


# ── Interview Chat ────────────────────────────────────────────────────────────

@router.post("/{session_id}/chat", response_model=ChatReply)
async def post_chat(
    session_id: str,
    body: ChatMessageIn,
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    user_msg = InterviewChatMessage(
        session_id=session_id, role="user", content=body.message
    )
    db.add(user_msg)
    await db.flush()

    # Last 10 messages for context
    history = (
        await db.execute(
            select(InterviewChatMessage)
            .where(InterviewChatMessage.session_id == session_id)
            .order_by(InterviewChatMessage.created_at.desc())
            .limit(10)
        )
    ).scalars().all()
    history = list(reversed(history))

    github_section = ""
    if session.github_context:
        github_section = f"\n\nCANDIDATE GITHUB:\n{_format_github_for_prompt(session.github_context)}"

    messages = [
        {
            "role": "system",
            "content": (
                f"You are an interview coach. Help the candidate prepare for "
                f"{session.job_title} at {session.company_name}. Be specific and concise."
                f"{github_section}"
            ),
        }
    ] + [{"role": m.role, "content": m.content} for m in history]

    reply_text = await groq_chat(messages, max_tokens=512)

    assistant_msg = InterviewChatMessage(
        session_id=session_id, role="assistant", content=reply_text
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)

    return ChatReply(
        response=reply_text,
        message=ChatMessageOut.model_validate(assistant_msg),
    )


@router.get("/{session_id}/chat", response_model=list[ChatMessageOut])
async def get_chat(session_id: str, db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(InterviewChatMessage)
            .where(InterviewChatMessage.session_id == session_id)
            .order_by(InterviewChatMessage.created_at)
        )
    ).scalars().all()
    return [ChatMessageOut.model_validate(r) for r in rows]


@router.delete("/{session_id}/chat/{message_id}")
async def delete_chat_message(
    session_id: str, message_id: str, db: AsyncSession = Depends(get_db)
):
    msg = await db.get(InterviewChatMessage, message_id)
    if not msg or msg.session_id != session_id:
        raise HTTPException(404, "Message not found")
    await db.delete(msg)
    await db.commit()
    return {"deleted": message_id}


@router.delete("/{session_id}/chat")
async def clear_chat(session_id: str, db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(InterviewChatMessage).where(InterviewChatMessage.session_id == session_id)
        )
    ).scalars().all()
    for r in rows:
        await db.delete(r)
    await db.commit()
    return {"cleared": len(rows)}


# ── Brainstorm Threads ────────────────────────────────────────────────────────

@router.post("/{session_id}/brainstorm/thread", response_model=BrainstormThreadOut)
async def create_thread(
    session_id: str,
    body: BrainstormThreadCreate,
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    thread = BrainstormThread(session_id=session_id, title=body.title)
    db.add(thread)
    await db.commit()
    await db.refresh(thread)
    return BrainstormThreadOut.model_validate(thread)


@router.get("/{session_id}/brainstorm/threads", response_model=list[BrainstormThreadOut])
async def list_threads(session_id: str, db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(BrainstormThread)
            .where(BrainstormThread.session_id == session_id)
            .order_by(BrainstormThread.created_at)
        )
    ).scalars().all()
    return [BrainstormThreadOut.model_validate(r) for r in rows]


@router.patch("/{session_id}/brainstorm/thread/{thread_id}", response_model=BrainstormThreadOut)
async def rename_thread(
    session_id: str,
    thread_id: str,
    body: BrainstormThreadRename,
    db: AsyncSession = Depends(get_db),
):
    thread = await db.get(BrainstormThread, thread_id)
    if not thread or thread.session_id != session_id:
        raise HTTPException(404, "Thread not found")
    thread.title = body.title
    await db.commit()
    await db.refresh(thread)
    return BrainstormThreadOut.model_validate(thread)


@router.delete("/{session_id}/brainstorm/thread/{thread_id}")
async def delete_thread(
    session_id: str, thread_id: str, db: AsyncSession = Depends(get_db)
):
    thread = await db.get(BrainstormThread, thread_id)
    if not thread or thread.session_id != session_id:
        raise HTTPException(404, "Thread not found")
    await db.delete(thread)
    await db.commit()
    return {"deleted": thread_id}


# ── Brainstorm Messages ───────────────────────────────────────────────────────

@router.post(
    "/{session_id}/brainstorm/thread/{thread_id}/message",
    response_model=BrainstormReply,
)
async def post_brainstorm_message(
    session_id: str,
    thread_id: str,
    body: ChatMessageIn,
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    thread = await db.get(BrainstormThread, thread_id)
    if not thread or thread.session_id != session_id:
        raise HTTPException(404, "Thread not found")

    user_msg = BrainstormMessage(thread_id=thread_id, role="user", content=body.message)
    db.add(user_msg)
    await db.flush()

    history = (
        await db.execute(
            select(BrainstormMessage)
            .where(BrainstormMessage.thread_id == thread_id)
            .order_by(BrainstormMessage.created_at.desc())
            .limit(10)
        )
    ).scalars().all()
    history = list(reversed(history))

    gh_section = ""
    if session.github_context:
        gh_section = f"\n\nCANDIDATE GITHUB:\n{_format_github_for_prompt(session.github_context)}"

    messages = [
        {
            "role": "system",
            "content": (
                f"You are a career strategist helping someone prepare for "
                f"{session.job_title} at {session.company_name}. Think creatively and practically."
                f"{gh_section}"
            ),
        }
    ] + [{"role": m.role, "content": m.content} for m in history]

    reply_text = await groq_chat(messages, max_tokens=512)

    assistant_msg = BrainstormMessage(
        thread_id=thread_id, role="assistant", content=reply_text
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)

    return BrainstormReply(
        response=reply_text,
        message=BrainstormMessageOut.model_validate(assistant_msg),
    )


@router.get(
    "/{session_id}/brainstorm/thread/{thread_id}/messages",
    response_model=list[BrainstormMessageOut],
)
async def get_brainstorm_messages(
    session_id: str, thread_id: str, db: AsyncSession = Depends(get_db)
):
    thread = await db.get(BrainstormThread, thread_id)
    if not thread or thread.session_id != session_id:
        raise HTTPException(404, "Thread not found")
    rows = (
        await db.execute(
            select(BrainstormMessage)
            .where(BrainstormMessage.thread_id == thread_id)
            .order_by(BrainstormMessage.created_at)
        )
    ).scalars().all()
    return [BrainstormMessageOut.model_validate(r) for r in rows]
