"""
Test script for the ATS pipeline.
- Real GitHub API calls (tests plumbing)
- Mocked Anthropic API calls (no token spend)
"""
from __future__ import annotations

import asyncio
import sys
import os
from unittest import mock

sys.path.insert(0, os.path.dirname(__file__))

SAMPLE_RESUME = """\
John Doe
john@example.com | github.com/achyutniroula | linkedin.com/in/johndoe

EDUCATION
University of Toronto
B.Sc. Computer Science    Sep 2020 – Apr 2024

EXPERIENCE
Software Developer    Acme Corp    May 2024 – Present
- Built REST APIs with Python and FastAPI
- Deployed services using Docker and GitHub Actions CI/CD
- Wrote async data pipelines with SQLAlchemy and PostgreSQL

SKILLS
Python, FastAPI, Docker, PostgreSQL, React, TypeScript, AWS, Git
"""

SAMPLE_JD = """\
Backend Software Engineer – Cloud Infrastructure

We are looking for a Backend Engineer to design and build scalable cloud services.

Required:
- 2+ years Python backend development (FastAPI or Django)
- Docker and Kubernetes container orchestration
- CI/CD pipelines (GitHub Actions, Jenkins)
- PostgreSQL or other relational databases
- AWS services (EC2, S3, Lambda, RDS)

Preferred:
- Experience with async Python (asyncio, httpx)
- Redis caching
- REST API design and OpenAPI specs
- Monitoring with Prometheus/Grafana

Responsibilities:
- Design and implement microservices APIs
- Manage Docker deployments on AWS ECS/EKS
- Write comprehensive test suites (pytest)
- Participate in code reviews and architecture discussions
"""

MOCK_JD_ANALYSIS = """\
ROLE_TITLE: Backend Software Engineer
REQUIRED_SKILLS: Python, FastAPI, Docker, Kubernetes, CI/CD, PostgreSQL, AWS
PREFERRED_SKILLS: asyncio, httpx, Redis, REST API, OpenAPI, pytest
RESPONSIBILITIES: Design microservices APIs, manage Docker deployments, write test suites, code reviews
SENIORITY: Mid-level, 2+ years
KEYWORDS: microservices, Docker, Kubernetes, CI/CD, AWS, FastAPI, PostgreSQL, asyncio, REST API, pytest, ECS, GitHub Actions, SQLAlchemy, async, backend
"""

MOCK_REWRITE = """\
John Doe
john@example.com | github.com/achyutniroula | linkedin.com/in/johndoe

EDUCATION
University of Toronto
B.Sc. Computer Science    Sep 2020 – Apr 2024

EXPERIENCE
Backend Software Engineer    Acme Corp    May 2024 – Present
- Designed and deployed microservices REST APIs with FastAPI serving production traffic
- Orchestrated Docker containers via GitHub Actions CI/CD pipelines to AWS ECS
- Implemented async SQLAlchemy data pipelines with PostgreSQL for high-throughput queries

SKILLS
Python, FastAPI, Docker, Kubernetes, PostgreSQL, AWS (EC2, S3, ECS), asyncio, httpx, GitHub Actions, pytest, React, TypeScript

PROJECTS
job-hunt | Python, FastAPI, TypeScript, Docker, SQLAlchemy, Claude API
- Built async job scraping microservices across 7 boards with concurrent httpx clients
- Deployed with Docker Compose; integrated CI/CD pipeline with GitHub Actions

indeed-stealth-scraper | Python, Playwright, asyncio, FastAPI
- Implemented async stealth scraper with exponential backoff and structured logging
- Validated API response schemas with pytest test suites and diagnostic HTML captures

Cloud-Chat | Python, FastAPI, React, Docker
- Designed real-time WebSocket chat API with async message handling and PostgreSQL persistence
- Deployed containerized services to AWS using Docker and GitHub Actions CI/CD

Inventory | Flask, Firebase, Google Cloud Run, Docker
- Built REST API with role-based access control deployed to Google Cloud Run via Docker
- Integrated Firebase Realtime Database with Chart.js dashboard for live inventory tracking

job-hunt-ai | Python, FastAPI, React, AWS, Docker
- Architected AI resume optimization pipeline using Claude API with async processing
- Deployed full-stack application with Docker Compose and automated CI/CD workflows

---CHANGES---
[ROLE] Renamed 'Software Developer' to 'Backend Software Engineer' | source: github:job-hunt
[BULLET] Added 'microservices' and 'AWS ECS' keywords | source: github:job-hunt
[BULLET] Added 'async SQLAlchemy' reference | source: github:job-hunt
[SKILL] Added Kubernetes, asyncio, httpx, GitHub Actions, pytest | source: github:job-hunt
[PROJECT] Selected 5 distinct repos aligned to Cloud/DevOps JD | source: github:multiple
"""

MOCK_LATEX = r"""\documentclass[letterpaper,11pt]{article}
% (full LaTeX omitted in mock)
\begin{document}
Mock LaTeX output for test
\end{document}"""


def _make_mock_anthropic():
    """Build a mock AsyncAnthropic client with pre-set call responses."""
    mock_client = mock.AsyncMock()

    def make_response(text: str):
        r = mock.MagicMock()
        r.content = [mock.MagicMock(text=text)]
        return r

    mock_client.messages.create = mock.AsyncMock(side_effect=[
        make_response(MOCK_JD_ANALYSIS),   # Step 1: JD analysis
        make_response(MOCK_REWRITE),        # Step 3: rewrite
        make_response(MOCK_LATEX),          # LaTeX generation
    ])
    return mock_client


async def main():
    print("=" * 60)
    print("STEP 1: GitHub Digest Ingestion (real API)")
    print("=" * 60)

    from app.services.github_ingestion import fetch_github_digest

    digest = await fetch_github_digest("https://github.com/achyutniroula")
    if digest is None:
        print("ERROR: fetch_github_digest returned None")
        sys.exit(1)

    print(f"Username:   @{digest.username}")
    print(f"Repos:      {len(digest.repos)}")
    print(f"Top langs:  {', '.join(list(digest.top_languages.keys())[:5])}")
    for r in digest.repos:
        dep_count = len(r.deps)
        cicd_count = len(r.cicd)
        src_count = len(r.source_files)
        print(f"  [{r.name}] lang:{r.primary_language} deps:{dep_count} cicd:{cicd_count} src:{src_count}")
    print()

    print("=" * 60)
    print("STEP 2: ATS Optimizer (mocked Claude)")
    print("=" * 60)

    from app.services.ats_optimizer import optimize_with_digest

    with mock.patch("app.services.ats_optimizer.anthropic.AsyncAnthropic") as mock_cls:
        mock_cls.return_value = _make_mock_anthropic()
        result = await optimize_with_digest(
            resume_text=SAMPLE_RESUME,
            job_description=SAMPLE_JD,
            github_digest=digest,
        )

    print(f"ATS score:  {result.ats_score_before} -> {result.ats_score_after}")
    print(f"Matched:    {len(result.matched_keywords)} keywords")
    print(f"Changes:    {len(result.change_items)} items")
    print(f"LaTeX:      {'yes' if result.latex_text else 'no'}")
    print()
    print("--- Optimized Resume (first 800 chars) ---")
    print(result.optimized_text[:800])
    print()

    print("=" * 60)
    print("STEP 3: Verify generate.py imports are intact")
    print("=" * 60)

    from app.api.routes.generate import router, cover_letter, cover_letter_docx, fetch_job_url
    print("cover_letter:      OK")
    print("cover_letter_docx: OK")
    print("fetch_job_url:     OK")
    print()
    print("All tests passed.")


if __name__ == "__main__":
    asyncio.run(main())
