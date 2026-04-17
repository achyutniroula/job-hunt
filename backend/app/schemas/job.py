from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, HttpUrl, model_validator


class JobBase(BaseModel):
    title: str
    company: str | None = None
    location: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None
    salary_interval: str | None = None
    description: str | None = None
    skills: list[str] = Field(default_factory=list)
    seniority_level: str | None = None
    employment_type: str | None = None
    is_remote: bool = False
    board: str
    job_url: str | None = None
    posted_at: datetime | None = None


class JobRead(JobBase):
    id: str
    session_id: str
    match_score: float | None = None
    archetype: str = ""
    fit_analysis: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def parse_skills_json(cls, data: Any) -> Any:
        """skills is stored as JSON string in DB; deserialize it."""
        import json

        if isinstance(data, dict):
            raw = data.get("skills")
            if isinstance(raw, str):
                try:
                    data["skills"] = json.loads(raw)
                except Exception:
                    data["skills"] = []
        return data


class ScrapeRequest(BaseModel):
    keywords: str = Field(..., min_length=1, max_length=256)
    location: str = Field(default="Canada", max_length=128)
    remote_only: bool = False
    boards: list[str] | None = None
    city: str | None = None
    distance_km: int = Field(default=100, ge=25, le=500)


class ScrapeSessionRead(BaseModel):
    id: str
    keywords: str
    location: str
    remote_only: bool
    boards: list[str] | None = None
    status: str
    job_count: int
    error: str | None = None
    resume_filename: str | None = None
    created_at: datetime
    finished_at: datetime | None = None

    model_config = {"from_attributes": True}


class JobFilter(BaseModel):
    min_match_score: float | None = None
    remote_only: bool | None = None
    boards: list[str] | None = None
    seniority: list[str] | None = None
    sort_by: str = "match_score"  # match_score | posted_at
