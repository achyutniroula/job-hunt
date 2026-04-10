import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ScrapeSession(Base):
    """Tracks a single scraping run initiated by the user."""

    __tablename__ = "scrape_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    # Search params
    keywords: Mapped[str] = mapped_column(String(512))
    location: Mapped[str] = mapped_column(String(256))
    remote_only: Mapped[bool] = mapped_column(default=False)
    boards: Mapped[str | None] = mapped_column(Text)   # JSON list

    # Status: pending | running | done | failed
    status: Mapped[str] = mapped_column(String(32), default="pending")
    job_count: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)

    # Resume reference (filename stored after upload)
    resume_filename: Mapped[str | None] = mapped_column(String(512))

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
