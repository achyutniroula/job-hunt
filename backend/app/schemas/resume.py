from __future__ import annotations

from pydantic import BaseModel, Field


class ParsedResume(BaseModel):
    """Structured representation of a parsed resume."""

    raw_text: str
    skills: list[str] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    experience_years: float | None = None
    seniority_level: str | None = None       # junior | mid | senior | lead | executive
    job_titles: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)


class ResumeUploadResponse(BaseModel):
    filename: str
    parsed: ParsedResume


class ATSOptimizeRequest(BaseModel):
    resume_filename: str
    job_id: str | None = None     # If provided, tailor to this job
    job_description: str | None = None   # Raw JD text (alternative to job_id)


class ATSOptimizeResponse(BaseModel):
    original_text: str
    optimized_text: str
    changes_summary: list[str]
    ats_score_before: int | None = None
    ats_score_after: int | None = None


class CoverLetterRequest(BaseModel):
    resume_filename: str
    job_id: str | None = None
    job_description: str | None = None
    company_name: str | None = None
    job_title: str | None = None
    extra_notes: str | None = Field(
        default=None,
        description="Any extra context the user wants included (e.g., referral name)",
    )


class CoverLetterResponse(BaseModel):
    cover_letter: str
    word_count: int
