"""Tests for fit_analyzer.py — mocks Groq, no real API calls."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from unittest.mock import AsyncMock, patch, MagicMock


def _mock_groq_response(content: str):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": content}}]
    }
    return mock_resp


_SAMPLE_GROQ_REPLY = (
    "GRADE: B+\n"
    "SUMMARY: Strong backend match with solid Python experience.\n"
    "STRENGTHS: Python | REST API | PostgreSQL\n"
    "GAPS: Kubernetes | GraphQL\n"
    "TIP: Highlight your FastAPI work and mention Docker experience prominently."
)


# ── extract_requirements ──────────────────────────────────────────────────────

def test_extract_with_header():
    from app.services.fit_analyzer import extract_requirements
    jd = (
        "About Us\nWe are a leading fintech company building the future of payments.\n\n"
        "Requirements:\n"
        "- 3+ years of Python experience with FastAPI or Django\n"
        "- Strong knowledge of REST API design and microservices architecture\n"
        "- Experience with PostgreSQL, Redis, and cloud platforms (AWS/GCP)\n"
        "- Familiarity with Docker, Kubernetes, and CI/CD pipelines\n\n"
        "What We Offer\n- Competitive salary\n- Health benefits\n- Remote work"
    )
    result = extract_requirements(jd)
    assert "Python" in result, "Requirements section should be extracted"
    assert "Competitive salary" not in result, "Benefits section should be excluded"
    print("PASS test_extract_with_header")


def test_extract_no_header_fallback():
    from app.services.fit_analyzer import extract_requirements
    jd = "A" * 2000
    result = extract_requirements(jd)
    assert len(result) <= 1500, "Should fall back to first 1500 chars"
    print("PASS test_extract_no_header_fallback")


def test_extract_tiny_section_fallback():
    from app.services.fit_analyzer import extract_requirements
    jd = "About Us\nBig company.\n\nRequirements:\nPython.\n\nWhat We Offer\nGreat pay."
    result = extract_requirements(jd)
    # Section is < 80 chars → falls back to full JD[:1500]
    assert "About Us" in result or "Requirements" in result
    print("PASS test_extract_tiny_section_fallback")


# ── detect_seniority ──────────────────────────────────────────────────────────

def test_detect_seniority():
    from app.services.fit_analyzer import detect_seniority
    assert detect_seniority("Junior Developer", "1-2 years experience") == "junior"
    assert detect_seniority("Senior Cloud Engineer", "8+ years required") == "senior"
    assert detect_seniority("Principal Architect", "Lead the team") == "lead"
    assert detect_seniority("Software Developer", "Build great software") == "any"
    print("PASS test_detect_seniority")


# ── detect_user_level ─────────────────────────────────────────────────────────

def test_detect_user_level():
    from app.services.fit_analyzer import detect_user_level
    resume = (
        "BSc Honours Computer Science expected graduation 2025\n"
        "1 year internship at Acme Corp 2024"
    )
    result = detect_user_level(resume)
    assert result == "student", f"Expected student, got {result}"
    print("PASS test_detect_user_level")


# ── _parse_fit_response ───────────────────────────────────────────────────────

def test_parse_fit_response():
    from app.services.fit_analyzer import _parse_fit_response
    parsed = _parse_fit_response(_SAMPLE_GROQ_REPLY, seniority="mid", user_level="junior")
    required_keys = {"grade", "seniority", "user_level", "summary", "strengths", "gaps", "tip"}
    assert required_keys == set(parsed.keys()), f"Missing keys: {required_keys - set(parsed.keys())}"
    assert parsed["grade"] == "B+"
    assert len(parsed["strengths"]) == 3
    assert len(parsed["gaps"]) == 2
    assert parsed["seniority"] == "mid"
    assert parsed["user_level"] == "junior"
    print("PASS test_parse_fit_response")


# ── analyze_fit never returns None ────────────────────────────────────────────

async def test_analyze_fit_never_none():
    from app.services.fit_analyzer import analyze_fit
    with patch("app.services.fit_analyzer.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=_mock_groq_response(_SAMPLE_GROQ_REPLY))
        mock_cls.return_value = mock_client
        with patch("app.services.fit_analyzer.get_settings") as mock_settings:
            mock_settings.return_value.groq_api_key = "test-key"
            result = await analyze_fit("Restaurant Cook", "Prepare food", "other", 0.1)
    assert result is not None, "analyze_fit must never return None"
    assert "grade" in result
    print("PASS test_analyze_fit_never_none")


async def test_analyze_fit_groq_failure_safe_defaults():
    from app.services.fit_analyzer import analyze_fit
    with patch("app.services.fit_analyzer.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(side_effect=Exception("network error"))
        mock_cls.return_value = mock_client
        with patch("app.services.fit_analyzer.get_settings") as mock_settings:
            mock_settings.return_value.groq_api_key = "test-key"
            result = await analyze_fit("SWE", "Build stuff", "Backend Engineer", 0.5)
    assert result is not None
    assert result["grade"] == "?"
    assert result["tip"] == "Apply anyway"
    print("PASS test_analyze_fit_groq_failure_safe_defaults")


# ── analyze_all_jobs — all 10 must have fit_analysis ─────────────────────────

async def test_analyze_all_jobs_no_nones():
    from app.services.fit_analyzer import analyze_all_jobs
    jobs = [
        {"id": str(i), "title": f"Job {i}", "description": "Backend Python role",
         "archetype": "Backend Engineer", "match_score": 0.6}
        for i in range(10)
    ]
    with patch("app.services.fit_analyzer.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=_mock_groq_response(_SAMPLE_GROQ_REPLY))
        mock_cls.return_value = mock_client
        with patch("app.services.fit_analyzer.get_settings") as mock_settings:
            mock_settings.return_value.groq_api_key = "test-key"
            result = await analyze_all_jobs(jobs, "Python developer with 3 years experience",
                                            batch_size=25, delay_between_batches=0)
    assert len(result) == 10, "All 10 jobs must be returned"
    for i, job in enumerate(result):
        assert job.get("fit_analysis") is not None, f"Job {i} has None fit_analysis"
        assert "grade" in job["fit_analysis"]
    print("PASS test_analyze_all_jobs_no_nones")


if __name__ == "__main__":
    test_extract_with_header()
    test_extract_no_header_fallback()
    test_extract_tiny_section_fallback()
    test_detect_seniority()
    test_detect_user_level()
    test_parse_fit_response()
    asyncio.run(test_analyze_fit_never_none())
    asyncio.run(test_analyze_fit_groq_failure_safe_defaults())
    asyncio.run(test_analyze_all_jobs_no_nones())
    print("\nAll fit_analyzer tests passed.")
