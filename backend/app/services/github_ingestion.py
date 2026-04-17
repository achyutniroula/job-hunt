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


# ── ATS-specific digest ingestion ─────────────────────────────────────────────

_DEP_BASENAMES = {
    "requirements.txt", "requirements-dev.txt", "requirements-test.txt",
    "pyproject.toml", "setup.py", "setup.cfg", "Pipfile",
    "package.json", "package-lock.json", "yarn.lock",
    "Cargo.toml", "go.mod", "go.sum",
    "pom.xml", "build.gradle", "build.gradle.kts",
    "composer.json", "Gemfile", "mix.exs",
}

_CICD_BASENAMES = {
    "Jenkinsfile", ".travis.yml", ".gitlab-ci.yml",
    "azure-pipelines.yml", "bitbucket-pipelines.yml",
}

_STEP_A_NAMES = {
    "main.py", "app.py", "server.py", "manage.py", "cli.py", "run.py",
    "index.ts", "index.js", "main.ts", "app.ts", "main.go", "main.rs",
    "lib.rs", "mod.rs",
}

_STEP_B_DIRS = {
    "src", "app", "lib", "core", "api", "services", "routes", "handlers",
    "controllers", "models", "schema", "schemas",
}

_STEP_B_EXTS = {".py", ".ts", ".js", ".go", ".rs", ".java", ".kt", ".swift", ".rb"}

_SKIP_DIRS = {
    "test", "tests", "__pycache__", "node_modules", "dist",
    "build", ".git", "vendor", "migrations", "alembic",
}


def _is_skip_path(path: str) -> bool:
    for part in path.split("/")[:-1]:
        if part.lower() in _SKIP_DIRS:
            return True
    return False


def _pick_source_files_full(all_paths: list[str]) -> list[str]:
    chosen: list[str] = []
    seen: set[str] = set()

    # Step A: exact name matches at root or one level deep
    name_to_path: dict[str, str] = {}
    for path in all_paths:
        basename = path.split("/")[-1]
        depth = path.count("/")
        if basename in _STEP_A_NAMES and depth <= 1:
            existing = name_to_path.get(basename)
            if existing is None or existing.count("/") > depth:
                name_to_path[basename] = path
    for name in _STEP_A_NAMES:
        if name in name_to_path and len(chosen) < 15:
            p = name_to_path[name]
            chosen.append(p)
            seen.add(p)

    # Step B: files in key directories
    if len(chosen) < 15:
        for path in all_paths:
            if path in seen:
                continue
            parts = path.split("/")
            if len(parts) < 2:
                continue
            parent_dir = parts[-2].lower()
            fname = parts[-1]
            ext = ("." + fname.rsplit(".", 1)[-1]) if "." in fname else ""
            if parent_dir in _STEP_B_DIRS and ext in _STEP_B_EXTS:
                chosen.append(path)
                seen.add(path)
                if len(chosen) >= 15:
                    break

    # Step C: any remaining code files not in skip dirs
    if len(chosen) < 15:
        for path in all_paths:
            if path in seen or _is_skip_path(path):
                continue
            fname = path.split("/")[-1]
            ext = ("." + fname.rsplit(".", 1)[-1]) if "." in fname else ""
            if ext in {".py", ".ts", ".js", ".go", ".rs", ".java", ".kt"}:
                chosen.append(path)
                seen.add(path)
                if len(chosen) >= 15:
                    break

    return chosen[:15]


@dataclass
class RepoDigest:
    name:             str
    description:      str | None
    primary_language: str | None
    languages:        dict[str, int]
    topics:           list[str]
    stars:            int
    forks:            int
    updated_at:       str
    is_pinned:        bool
    readme:           str | None
    file_tree:        list[str]
    deps:             dict[str, str]
    cicd:             dict[str, str]
    source_files:     dict[str, str]


def _serialize_repo(r: "RepoDigest", budget: int, pinned: set) -> str:
    total = sum(r.languages.values()) or 1
    lang_pct = ", ".join(
        f"{lang} {round(b / total * 100)}%"
        for lang, b in sorted(r.languages.items(), key=lambda x: -x[1])[:6]
    )
    pinned_tag = " [PINNED]" if r.name in pinned else ""

    lines = [
        f"--- REPO: {r.name}{pinned_tag} ---",
        f"Stars: {r.stars} | Forks: {r.forks} | Language: {r.primary_language} | Updated: {r.updated_at}",
        f"Description: {r.description or 'none'}",
        f"Topics: {', '.join(r.topics) or 'none'}",
        f"Languages: {lang_pct or 'none'}",
        "",
        f"FILE TREE ({len(r.file_tree)} files):",
        " | ".join(r.file_tree[:120]),
    ]
    if r.readme:
        lines += ["", "README:", r.readme]
    if r.deps:
        lines += ["", "DEPENDENCIES:"]
        for fname, content in r.deps.items():
            lines += [f"[{fname}]:", content]
    if r.cicd:
        lines += ["", "CI/CD:"]
        for fname, content in r.cicd.items():
            lines += [f"[{fname}]:", content]
    if r.source_files:
        lines += ["", "SOURCE FILES:"]
        for path, content in r.source_files.items():
            lines += [f"[{path}]:", content]

    serialized = "\n".join(lines)
    if len(serialized) <= budget:
        return serialized

    # Over budget: truncate readme to half, then hard-truncate
    if r.readme and len(r.readme) > 100:
        half = r.readme[: len(r.readme) // 2]
        lines2 = [
            f"--- REPO: {r.name}{pinned_tag} ---",
            f"Stars: {r.stars} | Forks: {r.forks} | Language: {r.primary_language} | Updated: {r.updated_at}",
            f"Description: {r.description or 'none'}",
            f"Topics: {', '.join(r.topics) or 'none'}",
            f"Languages: {lang_pct or 'none'}",
            "",
            f"FILE TREE ({len(r.file_tree)} files):",
            " | ".join(r.file_tree[:120]),
            "", "README:", half,
        ]
        if r.deps:
            lines2 += ["", "DEPENDENCIES:"]
            for fname, content in r.deps.items():
                lines2 += [f"[{fname}]:", content]
        if r.cicd:
            lines2 += ["", "CI/CD:"]
            for fname, content in r.cicd.items():
                lines2 += [f"[{fname}]:", content]
        if r.source_files:
            lines2 += ["", "SOURCE FILES:"]
            for path, content in r.source_files.items():
                lines2 += [f"[{path}]:", content]
        serialized = "\n".join(lines2)

    if len(serialized) <= budget:
        return serialized

    truncated = serialized[:budget]
    last_nl = truncated.rfind("\n")
    return truncated[:last_nl] if last_nl > 0 else truncated


@dataclass
class GitHubDigest:
    username:      str
    repos:         list[RepoDigest]
    top_languages: dict[str, int]
    pinned_repos:  list[str]
    total_repos:   int

    def repo_count(self) -> int:
        return len(self.repos)

    def to_context_string(self) -> str:
        TOTAL_CHAR_BUDGET = 180_000
        repos_count = len(self.repos)
        if repos_count == 0:
            return "No GitHub data."

        pinned = set(self.pinned_repos)
        base_budget = TOTAL_CHAR_BUDGET // repos_count
        budgets: dict[str, int] = {}
        for r in self.repos:
            budgets[r.name] = min(base_budget * 2, 12000) if r.name in pinned \
                              else min(base_budget, 8000)
        total_allocated = sum(budgets.values())
        if total_allocated > TOTAL_CHAR_BUDGET:
            scale = TOTAL_CHAR_BUDGET / total_allocated
            budgets = {k: max(1000, int(v * scale)) for k, v in budgets.items()}

        top_langs = ", ".join(list(self.top_languages.keys())[:10])
        header = (
            f"=== GITHUB: @{self.username} | {self.total_repos} public repos | "
            f"{self.repo_count()} non-fork repos fetched | "
            f"Top languages: {top_langs} ===\n"
            f"Pinned repos: {', '.join(self.pinned_repos) or 'none'}"
        )
        repo_parts = [_serialize_repo(r, budgets[r.name], pinned) for r in self.repos]
        return header + "\n\n" + "\n\n".join(repo_parts)


async def _fetch_repo_digest_full(
    client: httpx.AsyncClient,
    username: str,
    repo: dict,
) -> RepoDigest:
    name = repo["name"]
    default_branch = repo.get("default_branch", "main")
    is_pinned = repo.get("_is_pinned", False)

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

    langs: dict[str, int] = {}
    if not isinstance(lang_r, Exception) and lang_r.status_code == 200:
        langs = lang_r.json()

    readme: str | None = None
    if not isinstance(readme_r, Exception) and readme_r.status_code == 200:
        try:
            readme = base64.b64decode(readme_r.json().get("content", "")).decode("utf-8", errors="ignore")
        except Exception:
            pass

    all_paths: list[str] = []
    if not isinstance(tree_r, Exception) and tree_r.status_code == 200:
        all_paths = [
            item["path"]
            for item in tree_r.json().get("tree", [])
            if item.get("type") == "blob"
        ]

    dep_paths = [
        p for p in all_paths
        if p.split("/")[-1] in _DEP_BASENAMES and p.count("/") <= 2
    ]

    cicd_paths: list[str] = []
    for p in all_paths:
        basename = p.split("/")[-1]
        if ".github/workflows/" in p and p.endswith((".yml", ".yaml")):
            cicd_paths.append(p)
        elif basename in _CICD_BASENAMES and p.count("/") == 0:
            cicd_paths.append(p)
        elif p == "Makefile":
            cicd_paths.append(p)

    source_paths = _pick_source_files_full(all_paths)

    all_fetch = dep_paths + cicd_paths + source_paths
    if all_fetch:
        raw_contents = await asyncio.gather(
            *[_fetch_file_content(client, username, name, p) for p in all_fetch],
            return_exceptions=True,
        )
    else:
        raw_contents = []

    dep_end = len(dep_paths)
    cicd_end = dep_end + len(cicd_paths)

    deps: dict[str, str] = {}
    for path, content in zip(dep_paths, raw_contents[:dep_end]):
        if isinstance(content, str):
            basename = path.split("/")[-1]
            if basename == "package-lock.json":
                deps[basename] = "present (not fetched)"
            elif basename == "yarn.lock":
                deps[basename] = "\n".join(content.splitlines()[:50])
            elif basename == "go.sum":
                deps[basename] = "\n".join(content.splitlines()[:30])
            else:
                deps[basename] = content

    cicd: dict[str, str] = {}
    for path, content in zip(cicd_paths, raw_contents[dep_end:cicd_end]):
        if isinstance(content, str):
            cicd[path.split("/")[-1]] = content[:1500]

    source_files: dict[str, str] = {}
    for path, content in zip(source_paths, raw_contents[cicd_end:]):
        if isinstance(content, str) and content.strip():
            lines = content.splitlines()
            if len(lines) == 1 and len(lines[0]) > 500:
                continue
            source_files[path] = content[:2000]

    return RepoDigest(
        name=name,
        description=repo.get("description"),
        primary_language=repo.get("language"),
        languages=langs,
        topics=repo.get("topics", []),
        stars=repo.get("stargazers_count", 0),
        forks=repo.get("forks_count", 0),
        updated_at=repo.get("updated_at", ""),
        is_pinned=is_pinned,
        readme=readme,
        file_tree=all_paths,
        deps=deps,
        cicd=cicd,
        source_files=source_files,
    )


async def fetch_github_digest(url_or_username: str) -> GitHubDigest | None:
    """Fetch full-depth GitHub digest for ATS optimization. Fetches ALL non-fork repos."""
    username = _extract_username(url_or_username)
    if not username:
        return None
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Fetch pinned repos via GraphQL
            pinned_names: list[str] = []
            token = get_settings().github_token
            if token:
                try:
                    gql_r = await client.post(
                        "https://api.github.com/graphql",
                        json={
                            "query": (
                                "query($login: String!) { user(login: $login) { "
                                "pinnedItems(first: 6, types: REPOSITORY) { "
                                "nodes { ... on Repository { name } } } } }"
                            ),
                            "variables": {"login": username},
                        },
                        headers={**_headers(), "Content-Type": "application/json"},
                    )
                    if gql_r.status_code == 200:
                        nodes = (
                            gql_r.json()
                            .get("data", {})
                            .get("user", {})
                            .get("pinnedItems", {})
                            .get("nodes", [])
                        )
                        pinned_names = [n["name"] for n in nodes if n and "name" in n]
                except Exception as exc:
                    logger.warning("GraphQL pinned repos failed for %s: %s", username, exc)
            else:
                logger.warning("No GITHUB_TOKEN — skipping GraphQL pinned repos for %s", username)

            # Fetch ALL repos with Link-header pagination
            all_repos: list[dict] = []
            next_url: str | None = f"{_BASE}/users/{username}/repos"
            params: dict = {"per_page": 100, "sort": "updated"}
            while next_url:
                resp = await client.get(next_url, headers=_headers(), params=params)
                if resp.status_code in (403, 429):
                    logger.warning("GitHub rate limit for digest %s", username)
                    return GitHubDigest(
                        username=username, repos=[], top_languages={},
                        pinned_repos=pinned_names, total_repos=0,
                    )
                if resp.status_code != 200:
                    return None
                all_repos.extend(resp.json())
                next_url = None
                params = {}
                for part in resp.headers.get("Link", "").split(","):
                    if 'rel="next"' in part:
                        m = re.search(r"<([^>]+)>", part)
                        if m:
                            next_url = m.group(1)
                            break

            total_repos = len(all_repos)
            pinned_set = set(pinned_names)

            own_repos = [
                r for r in all_repos
                if not r.get("fork", False)
                and (r.get("visibility") == "public" or not r.get("private", False))
            ]
            for r in own_repos:
                r["_is_pinned"] = r["name"] in pinned_set

            async def _safe_fetch(repo: dict) -> RepoDigest | None:
                try:
                    return await _fetch_repo_digest_full(client, username, repo)
                except Exception as exc:
                    logger.warning("Digest failed for %s/%s: %s", username, repo["name"], exc)
                    return None

            results = await asyncio.gather(*[_safe_fetch(r) for r in own_repos])
            repo_digests = [d for d in results if d is not None]

            lang_totals: dict[str, int] = {}
            for r in repo_digests:
                for lang, b in r.languages.items():
                    lang_totals[lang] = lang_totals.get(lang, 0) + b
            top_langs = dict(sorted(lang_totals.items(), key=lambda x: x[1], reverse=True))

            return GitHubDigest(
                username=username,
                repos=repo_digests,
                top_languages=top_langs,
                pinned_repos=pinned_names,
                total_repos=total_repos,
            )
    except Exception as exc:
        logger.warning("GitHub digest failed: %s", exc)
        return None
