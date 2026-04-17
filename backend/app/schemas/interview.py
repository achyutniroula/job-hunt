from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


# ── Session ───────────────────────────────────────────────────────────────────

class InterviewSessionCreate(BaseModel):
    job_title: str
    job_description: str
    company_name: str
    resume_text: str
    github_url: str | None = None
    salary_info: str | None = None
    location: str | None = None
    seniority: str | None = None


class InterviewSessionOut(BaseModel):
    id: str
    job_title: str
    job_description: str
    company_name: str
    company_website: str | None
    company_careers_url: str | None
    company_glassdoor_url: str | None
    company_linkedin_url: str | None
    company_indeed_url: str | None
    resume_pdf_path: str | None
    resume_text: str | None
    github_url: str | None
    github_context: str | None
    salary_info: str | None
    location: str | None
    seniority: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InterviewSessionSummary(BaseModel):
    id: str
    job_title: str
    company_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Q&A ───────────────────────────────────────────────────────────────────────

class InterviewQAOut(BaseModel):
    id: str
    session_id: str
    category: str
    question: str
    answer: str
    order_index: int

    model_config = {"from_attributes": True}


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatMessageIn(BaseModel):
    message: str


class ChatMessageOut(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatReply(BaseModel):
    response: str
    message: ChatMessageOut


# ── Brainstorm Thread ─────────────────────────────────────────────────────────

class BrainstormThreadCreate(BaseModel):
    title: str


class BrainstormThreadRename(BaseModel):
    title: str


class BrainstormThreadOut(BaseModel):
    id: str
    session_id: str
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Brainstorm Message ────────────────────────────────────────────────────────

class BrainstormMessageOut(BaseModel):
    id: str
    thread_id: str
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class BrainstormReply(BaseModel):
    response: str
    message: BrainstormMessageOut


# ── Session updates ───────────────────────────────────────────────────────────

class SessionResumeUpdate(BaseModel):
    resume_text: str


class SessionRename(BaseModel):
    job_title: str
