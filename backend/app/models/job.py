import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(String(36), index=True)

    # Core fields
    title: Mapped[str] = mapped_column(String(512))
    company: Mapped[str | None] = mapped_column(String(256))
    location: Mapped[str | None] = mapped_column(String(256))
    salary_min: Mapped[float | None] = mapped_column(Float)
    salary_max: Mapped[float | None] = mapped_column(Float)
    salary_currency: Mapped[str | None] = mapped_column(String(8))
    salary_interval: Mapped[str | None] = mapped_column(String(32))

    # Content
    description: Mapped[str | None] = mapped_column(Text)
    skills: Mapped[str | None] = mapped_column(Text)          # JSON list
    seniority_level: Mapped[str | None] = mapped_column(String(64))
    employment_type: Mapped[str | None] = mapped_column(String(64))
    is_remote: Mapped[bool | None] = mapped_column(default=False)

    # Source
    board: Mapped[str] = mapped_column(String(64), index=True)
    job_url: Mapped[str | None] = mapped_column(Text)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Matching
    match_score: Mapped[float | None] = mapped_column(Float)
    archetype: Mapped[str] = mapped_column(String(64), default="")
    fit_analysis: Mapped[str | None] = mapped_column(Text)   # JSON dict

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
