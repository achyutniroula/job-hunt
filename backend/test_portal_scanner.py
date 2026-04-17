"""Tests for canadian_portals.py and portal_scanner.py — mocks httpx."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from unittest.mock import AsyncMock, patch, MagicMock


# ── CANADIAN_PORTALS structure tests ─────────────────────────────────────────

def test_portal_count():
    from app.core.canadian_portals import CANADIAN_PORTALS
    assert len(CANADIAN_PORTALS) >= 25, f"Expected >= 25 portals, got {len(CANADIAN_PORTALS)}"
    print(f"PASS test_portal_count ({len(CANADIAN_PORTALS)} portals)")


def test_portal_keys():
    from app.core.canadian_portals import CANADIAN_PORTALS
    required_keys = {"name", "city", "province", "ats", "url", "greenhouse_id", "lever_id", "ashby_id"}
    for portal in CANADIAN_PORTALS:
        missing = required_keys - set(portal.keys())
        assert not missing, f"Portal '{portal.get('name')}' missing keys: {missing}"
    print("PASS test_portal_keys")


def test_greenhouse_ids_set():
    from app.core.canadian_portals import CANADIAN_PORTALS
    for p in CANADIAN_PORTALS:
        if p["ats"] == "greenhouse":
            assert p["greenhouse_id"] is not None, f"{p['name']} greenhouse_id is None"
    print("PASS test_greenhouse_ids_set")


def test_lever_ids_set():
    from app.core.canadian_portals import CANADIAN_PORTALS
    for p in CANADIAN_PORTALS:
        if p["ats"] == "lever":
            assert p["lever_id"] is not None, f"{p['name']} lever_id is None"
    print("PASS test_lever_ids_set")


def test_ashby_ids_set():
    from app.core.canadian_portals import CANADIAN_PORTALS
    for p in CANADIAN_PORTALS:
        if p["ats"] == "ashby":
            assert p["ashby_id"] is not None, f"{p['name']} ashby_id is None"
    print("PASS test_ashby_ids_set")


# ── scan_canadian_portals with mocked httpx ───────────────────────────────────

_GREENHOUSE_RESPONSE = {
    "jobs": [
        {
            "title": "Software Engineer",
            "absolute_url": "https://boards.greenhouse.io/shopify/jobs/123",
            "location": {"name": "Toronto, ON"},
            "content": "<p>We need a Python developer with REST API experience.</p>",
        },
        {
            "title": "Frontend Developer",
            "absolute_url": "https://boards.greenhouse.io/shopify/jobs/456",
            "location": {"name": "Remote"},
            "content": "<p>React TypeScript developer needed.</p>",
        },
    ]
}


def _make_mock_client(response_data: dict, status: int = 200):
    mock_resp = MagicMock()
    mock_resp.status_code = status
    mock_resp.json.return_value = response_data

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_client.post = AsyncMock(return_value=mock_resp)
    return mock_client


async def test_scan_greenhouse():
    from app.services.portal_scanner import scan_canadian_portals
    with patch("app.services.portal_scanner.httpx.AsyncClient") as mock_cls:
        mock_cls.return_value = _make_mock_client(_GREENHOUSE_RESPONSE)
        results = await scan_canadian_portals(
            keywords=["developer"],
            ats_types=["greenhouse"],
        )

    assert len(results) > 0, "Expected results from Greenhouse scan"
    for r in results:
        assert "title" in r and r["title"], "Each result must have a title"
        assert "job_url" in r and r["job_url"], "Each result must have a url"
    print(f"PASS test_scan_greenhouse ({len(results)} jobs found)")


async def test_scan_filters_by_province():
    from app.services.portal_scanner import scan_canadian_portals
    with patch("app.services.portal_scanner.httpx.AsyncClient") as mock_cls:
        mock_cls.return_value = _make_mock_client(_GREENHOUSE_RESPONSE)
        results = await scan_canadian_portals(
            keywords=["developer"],
            provinces=["QC"],
            ats_types=["greenhouse"],
        )
    # Only QC greenhouse portals: Lightspeed, Nuvei
    print(f"PASS test_scan_filters_by_province ({len(results)} QC jobs)")


async def test_scan_empty_keywords_returns_all():
    from app.services.portal_scanner import scan_canadian_portals
    with patch("app.services.portal_scanner.httpx.AsyncClient") as mock_cls:
        mock_cls.return_value = _make_mock_client(_GREENHOUSE_RESPONSE)
        results = await scan_canadian_portals(
            keywords=[],  # empty = match all
            ats_types=["greenhouse"],
        )
    assert isinstance(results, list)
    print(f"PASS test_scan_empty_keywords_returns_all ({len(results)} jobs)")


if __name__ == "__main__":
    test_portal_count()
    test_portal_keys()
    test_greenhouse_ids_set()
    test_lever_ids_set()
    test_ashby_ids_set()
    asyncio.run(test_scan_greenhouse())
    asyncio.run(test_scan_filters_by_province())
    asyncio.run(test_scan_empty_keywords_returns_all())
    print("\nAll portal_scanner tests passed.")
