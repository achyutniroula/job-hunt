from __future__ import annotations

from pydantic import BaseModel, Field


class ParsedResume(BaseModel):
    raw_text: str
    skills: list[str] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    experience_years: float | None = None
    seniority_level: str | None = None
    job_titles: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)


class ResumeUploadResponse(BaseModel):
    filename: str
    parsed: ParsedResume


class ChangeItem(BaseModel):
    """A single categorized change made during optimization."""
    category: str   # verb | keyword | title | skill | metric | removed | reframe | restructure
    text: str


class ATSOptimizeRequest(BaseModel):
    resume_filename: str
    job_id: str | None = None
    job_description: str | None = None
    previous_optimized: str | None = None
    previous_improvements: list[str] | None = None
    github_urls: list[str] | None = None
    linkedin_url: str | None = None


class ATSOptimizeResponse(BaseModel):
    original_text: str
    optimized_text: str
    latex_text: str | None = None
    changes_summary: list[str] = []
    change_items: list[ChangeItem] = []
    ats_score_before: int | None = None
    ats_score_after: int | None = None
    matched_keywords: list[str] = []
    missing_keywords: list[str] = []
    improvements: list[str] = []
    transparency_report: str = ""
    interview_prep: str = ""
    gap_analysis: str = ""
    linkedin_unavailable: bool = False
    role_reframes: list[dict] = []


class CoverLetterRequest(BaseModel):
    resume_filename: str
    job_id: str | None = None
    job_description: str | None = None
    company_name: str | None = None
    job_title: str | None = None
    extra_notes: str | None = Field(default=None)


class CoverLetterResponse(BaseModel):
    cover_letter: str
    word_count: int
