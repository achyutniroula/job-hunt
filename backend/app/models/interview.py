import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str | None] = mapped_column(String(256))
    job_title: Mapped[str] = mapped_column(String(512))
    job_description: Mapped[str] = mapped_column(Text)
    company_name: Mapped[str] = mapped_column(String(256))
    company_website: Mapped[str | None] = mapped_column(Text)
    company_careers_url: Mapped[str | None] = mapped_column(Text)
    company_glassdoor_url: Mapped[str | None] = mapped_column(Text)
    company_linkedin_url: Mapped[str | None] = mapped_column(Text)
    company_indeed_url: Mapped[str | None] = mapped_column(Text)
    resume_pdf_path: Mapped[str | None] = mapped_column(Text)
    resume_text: Mapped[str | None] = mapped_column(Text)
    github_url: Mapped[str | None] = mapped_column(Text)
    github_context: Mapped[str | None] = mapped_column(Text)  # JSON string
    optimize_result: Mapped[str | None] = mapped_column(Text)  # JSON: ATSOptimizeResponse
    salary_info: Mapped[str | None] = mapped_column(String(256))
    location: Mapped[str | None] = mapped_column(String(256))
    seniority: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    qa: Mapped[list["InterviewQA"]] = relationship(
        "InterviewQA", back_populates="session", cascade="all, delete-orphan"
    )
    chat_messages: Mapped[list["InterviewChatMessage"]] = relationship(
        "InterviewChatMessage", back_populates="session", cascade="all, delete-orphan"
    )
    brainstorm_threads: Mapped[list["BrainstormThread"]] = relationship(
        "BrainstormThread", back_populates="session", cascade="all, delete-orphan"
    )


class InterviewQA(Base):
    __tablename__ = "interview_qa"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("interview_sessions.id"), index=True
    )
    category: Mapped[str] = mapped_column(String(64))
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    session: Mapped["InterviewSession"] = relationship("InterviewSession", back_populates="qa")


class InterviewChatMessage(Base):
    __tablename__ = "interview_chat_messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("interview_sessions.id"), index=True
    )
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    session: Mapped["InterviewSession"] = relationship(
        "InterviewSession", back_populates="chat_messages"
    )


class BrainstormThread(Base):
    __tablename__ = "brainstorm_threads"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("interview_sessions.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    session: Mapped["InterviewSession"] = relationship(
        "InterviewSession", back_populates="brainstorm_threads"
    )
    messages: Mapped[list["BrainstormMessage"]] = relationship(
        "BrainstormMessage", back_populates="thread", cascade="all, delete-orphan"
    )


class BrainstormMessage(Base):
    __tablename__ = "brainstorm_messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    thread_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("brainstorm_threads.id"), index=True
    )
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    thread: Mapped["BrainstormThread"] = relationship(
        "BrainstormThread", back_populates="messages"
    )
