"""Tests for archetype_detector.py — mocks Groq, no real API calls."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from unittest.mock import AsyncMock, patch, MagicMock

# ── Helpers ───────────────────────────────────────────────────────────────────

def _mock_groq_response(label: str):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": label}}]
    }
    return mock_resp


async def _call_detect(title: str, description: str, mock_label: str) -> str:
    from app.services.archetype_detector import detect_archetype
    with patch("app.services.archetype_detector.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=_mock_groq_response(mock_label))
        mock_client_cls.return_value = mock_client
        with patch("app.services.archetype_detector.get_settings") as mock_settings:
            mock_settings.return_value.groq_api_key = "test-key"
            return await detect_archetype(title, description)


# ── Tests ─────────────────────────────────────────────────────────────────────

async def test_cloud_devops():
    result = await _call_detect(
        "Senior DevOps Engineer",
        "We need Kubernetes, Terraform, AWS, CI/CD experience.",
        "Cloud/DevOps Engineer",
    )
    assert result == "Cloud/DevOps Engineer", f"Expected Cloud/DevOps Engineer, got {result}"
    print("PASS test_cloud_devops")


async def test_backend():
    result = await _call_detect(
        "Backend Software Engineer",
        "Build REST APIs with Python FastAPI and PostgreSQL.",
        "Backend Engineer",
    )
    assert result == "Backend Engineer", f"Expected Backend Engineer, got {result}"
    print("PASS test_backend")


async def test_frontend():
    result = await _call_detect(
        "Frontend Developer",
        "React, TypeScript, CSS, responsive design, accessibility.",
        "Frontend Engineer",
    )
    assert result == "Frontend Engineer", f"Expected Frontend Engineer, got {result}"
    print("PASS test_frontend")


async def test_invalid_label_falls_back_to_other():
    result = await _call_detect(
        "Barista",
        "Make coffee and serve customers.",
        "Barista",  # not a valid label
    )
    assert result == "Other", f"Expected Other for invalid label, got {result}"
    print("PASS test_invalid_label_falls_back_to_other")


def test_archetype_weights():
    from app.services.archetype_detector import ARCHETYPE_WEIGHTS, get_archetype_weights
    for label in [
        "Cloud/DevOps Engineer", "Backend Engineer", "Frontend Engineer",
        "Full Stack Engineer", "Data Engineer", "ML/AI Engineer",
        "Cybersecurity Analyst", "Systems/Infrastructure", "Software Developer", "Other",
    ]:
        assert label in ARCHETYPE_WEIGHTS, f"Missing archetype: {label}"
        weights = get_archetype_weights(label)
        assert "high" in weights and "medium" in weights, f"Missing keys for {label}"
    print("PASS test_archetype_weights")


if __name__ == "__main__":
    test_archetype_weights()
    asyncio.run(test_cloud_devops())
    asyncio.run(test_backend())
    asyncio.run(test_frontend())
    asyncio.run(test_invalid_label_falls_back_to_other())
    print("\nAll archetype tests passed.")
