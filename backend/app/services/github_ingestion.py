from __future__ import annotations

import asyncio
import base64
import logging
import re
from dataclasses import dataclass, field

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
_BASE = "https://api.github.com"

# Files that reveal what a project does and how it's built
_KEY_FILE_NAMES = [
    "requirements.txt", "requirements-dev.txt", "pyproject.toml",
    "package.json", "Cargo.toml", "go.mod", "pom.xml",
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "main.py", "app.py", "server.py", "manage.py", "cli.py",
    "index.ts", "index.js", "main.ts", "app.ts", "main.go", "main.rs",
]


def _headers() -> dict:
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    token = get_settings().github_token
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _extract_username(url_or_name: str) -> str:
    m = re.search(r"github\.com/([^/?\s]+)", url_or_name)
    return m.group(1) if m else url_or_name.strip().lstrip("@")


def _pick_key_files(all_paths: list[str]) -> list[str]:
    """Pick up to 5 most informative files from the repo tree."""
    chosen: list[str] = []
    name_to_path: dict[str, str] = {}

    for path in all_paths:
        basename = path.split("/")[-1]
        depth = path.count("/")
        # Prefer root-level (depth=0) then one level deep (depth=1)
        if basename in _KEY_FILE_NAMES:
            existing = name_to_path.get(basename)
            if existing is None or existing.count("/") > depth:
                name_to_path[basename] = path

    # Order by priority list
    for name in _KEY_FILE_NAMES:
        if name in name_to_path:
            chosen.append(name_to_path[name])
            if len(chosen) >= 5:
                break

    return chosen


@dataclass
class RepoSummary:
    name: str
    description: str | None
    languages: dict[str, int]
    topics: list[str]
    readme: str | None
    file_tree: list[str]          # up to 80 paths
    key_files: dict[str, str]     # path -> decoded content (truncated)
    stars: int
    forks: int
    updated_at: str


@dataclass
class GitHubProfile:
    username: str
    repos: list[RepoSummary]
    top_languages: dict[str, int]
    total_repos: int


async def _fetch_file_content(client: httpx.AsyncClient, username: str, repo: str, path: str) -> str | None:
    try:
        r = await client.get(f"{_BASE}/repos/{username}/{repo}/contents/{path}", headers=_headers())
        if r.status_code != 200:
            return None
        content = r.json().get("content", "")
        return base64.b64decode(content).decode("utf-8", errors="ignore")[:3000]
    except Exception:
        return None


async def _fetch_repo_detail(client: httpx.AsyncClient, username: str, repo: dict) -> RepoSummary:
    name = repo["name"]
    default_branch = repo.get("default_branch", "main")

    # Parallel: languages + readme + file tree
    lang_r, readme_r, tree_r = await asyncio.gather(
        client.get(f"{_BASE}/repos/{username}/{name}/languages", headers=_headers()),
        client.get(f"{_BASE}/repos/{username}/{name}/readme", headers=_headers()),
        client.get(
            f"{_BASE}/repos/{username}/{name}/git/trees/{default_branch}",
            headers=_headers(),
            params={"recursive": "1"},
        ),
        return_exceptions=True,
    )

    # Languages
    langs: dict[str, int] = {}
    if not isinstance(lang_r, Exception) and lang_r.status_code == 200:
        langs = lang_r.json()

    # README (up to 5000 chars)
    readme: str | None = None
    if not isinstance(readme_r, Exception) and readme_r.status_code == 200:
        try:
            raw = base64.b64decode(readme_r.json().get("content", "")).decode("utf-8", errors="ignore")
            readme = raw[:5000]
        except Exception:
            pass

    # File tree
    file_tree: list[str] = []
    key_file_paths: list[str] = []
    if not isinstance(tree_r, Exception) and tree_r.status_code == 200:
        blobs = [
            item["path"]
            for item in tree_r.json().get("tree", [])
            if item.get("type") == "blob"
        ]
        file_tree = blobs[:80]
        key_file_paths = _pick_key_files(blobs)

    # Fetch key files in parallel
    key_files: dict[str, str] = {}
    if key_file_paths:
        contents = await asyncio.gather(
            *[_fetch_file_content(client, username, name, p) for p in key_file_paths],
            return_exceptions=True,
        )
        for path, content in zip(key_file_paths, contents):
            if isinstance(content, str):
                key_files[path] = content

    return RepoSummary(
        name=name,
        description=repo.get("description"),
        languages=langs,
        topics=repo.get("topics", []),
        readme=readme,
        file_tree=file_tree,
        key_files=key_files,
        stars=repo.get("stargazers_count", 0),
        forks=repo.get("forks_count", 0),
        updated_at=repo.get("updated_at", ""),
    )


async def fetch_github_profile(url_or_username: str) -> GitHubProfile | None:
    username = _extract_username(url_or_username)
    if not username:
        return None
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
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
            sorted_repos = sorted(
                all_repos,
                key=lambda r: r.get("stargazers_count", 0) * 2 + (1 if r.get("updated_at") else 0),
                reverse=True,
            )
            own_repos = [r for r in sorted_repos if not r.get("fork", False)]
            to_fetch = own_repos if own_repos else sorted_repos

            details = await asyncio.gather(
                *[_fetch_repo_detail(client, username, r) for r in to_fetch],
                return_exceptions=True,
            )
            repo_summaries = [d for d in details if isinstance(d, RepoSummary)]

            lang_totals: dict[str, int] = {}
            for r in repo_summaries:
                for lang, b in r.languages.items():
                    lang_totals[lang] = lang_totals.get(lang, 0) + b
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
