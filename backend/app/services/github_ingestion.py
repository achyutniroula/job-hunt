from __future__ import annotations

import asyncio
import base64
import logging
import os
import re
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)

_GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
_BASE = "https://api.github.com"


def _headers() -> dict:
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if _GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {_GITHUB_TOKEN}"
    return h


def _extract_username(url_or_name: str) -> str:
    m = re.search(r"github\.com/([^/?\s]+)", url_or_name)
    return m.group(1) if m else url_or_name.strip().lstrip("@")


@dataclass
class RepoSummary:
    name: str
    description: str | None
    languages: dict[str, int]
    topics: list[str]
    readme_excerpt: str | None
    stars: int
    forks: int
    updated_at: str


@dataclass
class GitHubProfile:
    username: str
    repos: list[RepoSummary]
    top_languages: dict[str, int]
    total_repos: int


async def _fetch_repo_detail(client: httpx.AsyncClient, username: str, repo: dict) -> RepoSummary:
    name = repo["name"]
    langs: dict[str, int] = {}
    readme: str | None = None
    try:
        lr, rr = await asyncio.gather(
            client.get(f"{_BASE}/repos/{username}/{name}/languages", headers=_headers()),
            client.get(f"{_BASE}/repos/{username}/{name}/readme", headers=_headers()),
            return_exceptions=True,
        )
        if not isinstance(lr, Exception) and lr.status_code == 200:
            langs = lr.json()
        if not isinstance(rr, Exception) and rr.status_code == 200:
            content = rr.json().get("content", "")
            decoded = base64.b64decode(content).decode("utf-8", errors="ignore")
            readme = decoded[:1500]
    except Exception:
        pass
    return RepoSummary(
        name=name,
        description=repo.get("description"),
        languages=langs,
        topics=repo.get("topics", []),
        readme_excerpt=readme,
        stars=repo.get("stargazers_count", 0),
        forks=repo.get("forks_count", 0),
        updated_at=repo.get("updated_at", ""),
    )


async def fetch_github_profile(url_or_username: str) -> GitHubProfile | None:
    username = _extract_username(url_or_username)
    if not username:
        return None
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{_BASE}/users/{username}/repos",
                headers=_headers(),
                params={"per_page": 100, "sort": "updated"},
            )
            if resp.status_code in (403, 429):
                logger.warning("GitHub rate limit for %s", username)
                return GitHubProfile(username=username, repos=[], top_languages={}, total_repos=0)
            if resp.status_code != 200:
                return None
            all_repos = resp.json()

            # Pick top 8 by recency (already sorted) biased toward starred
            sorted_repos = sorted(all_repos, key=lambda r: r.get("stargazers_count", 0) + (1 if r.get("updated_at") else 0), reverse=True)
            top8 = sorted_repos[:8]

            details = await asyncio.gather(
                *[_fetch_repo_detail(client, username, r) for r in top8],
                return_exceptions=True,
            )
            repo_summaries = [d for d in details if isinstance(d, RepoSummary)]

            # Aggregate languages
            lang_totals: dict[str, int] = {}
            for r in repo_summaries:
                for lang, bytes_ in r.languages.items():
                    lang_totals[lang] = lang_totals.get(lang, 0) + bytes_
            top_langs = dict(sorted(lang_totals.items(), key=lambda x: x[1], reverse=True))

            return GitHubProfile(
                username=username,
                repos=repo_summaries,
                top_languages=top_langs,
                total_repos=len(all_repos),
            )
    except Exception as exc:
        logger.warning("GitHub ingestion failed: %s", exc)
        return None
