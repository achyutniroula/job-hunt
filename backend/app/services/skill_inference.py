from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.services.github_ingestion import GitHubProfile
from app.services.linkedin_ingestion import LinkedInProfile

_DEVOPS_TOPICS = {"docker", "ci", "cd", "github-actions", "kubernetes", "terraform", "ansible"}
_CLOUD_KEYWORDS = {"deployed", "production", "aws", "gcp", "azure", "heroku", "vercel"}
_DOMAIN_MAP = {
    "web": {"javascript", "typescript", "react", "vue", "angular", "html", "css", "node.js", "nextjs", "express"},
    "data": {"python", "r", "pandas", "numpy", "tensorflow", "pytorch", "jupyter", "sql", "spark"},
    "devops": {"docker", "kubernetes", "terraform", "ansible", "bash", "shell"},
    "mobile": {"swift", "kotlin", "dart", "flutter", "react native"},
    "systems": {"c", "c++", "rust", "go", "assembly"},
}


@dataclass
class UserSkillProfile:
    confirmed_skills: list[str] = field(default_factory=list)
    inferred_skills: list[str] = field(default_factory=list)
    project_evidence: dict[str, list[str]] = field(default_factory=dict)
    seniority_signals: list[str] = field(default_factory=list)
    experience_years_estimate: Optional[int] = None
    domains: list[str] = field(default_factory=list)


def infer_skill_profile(
    github: GitHubProfile | None,
    linkedin: LinkedInProfile | None,
) -> UserSkillProfile:
    profile = UserSkillProfile()

    if github:
        # Count language appearances across repos
        lang_count: dict[str, int] = {}
        lang_repos: dict[str, list[str]] = {}
        for repo in github.repos:
            for lang in repo.languages:
                lang_count[lang] = lang_count.get(lang, 0) + 1
                lang_repos.setdefault(lang, []).append(repo.name)

        for lang, count in lang_count.items():
            if count >= 3:
                profile.confirmed_skills.append(lang)
            else:
                profile.inferred_skills.append(lang)
            profile.project_evidence[lang] = lang_repos[lang]

        # Topic-based inference
        all_topics: set[str] = set()
        for repo in github.repos:
            all_topics.update(t.lower() for t in repo.topics)

        if all_topics & _DEVOPS_TOPICS:
            hit = sorted(all_topics & _DEVOPS_TOPICS)
            profile.inferred_skills.append("DevOps")
            profile.project_evidence["DevOps"] = list(hit)

        # README-based cloud inference
        cloud_repos: list[str] = []
        for repo in github.repos:
            readme = (repo.readme_excerpt or "").lower()
            if any(kw in readme for kw in _CLOUD_KEYWORDS):
                cloud_repos.append(repo.name)
        if cloud_repos:
            profile.inferred_skills.append("Cloud deployment")
            profile.project_evidence["Cloud deployment"] = cloud_repos

        # Notable projects
        notable = [r.name for r in github.repos if r.stars >= 5 or r.forks >= 2]
        if notable:
            profile.seniority_signals.append(f"Notable projects: {', '.join(notable[:4])}")
        if github.total_repos >= 10:
            profile.seniority_signals.append(f"{github.total_repos} public repos on GitHub")
        readme_count = sum(1 for r in github.repos if r.readme_excerpt and len(r.readme_excerpt) > 100)
        if readme_count >= 3:
            profile.seniority_signals.append(f"{readme_count} projects with documented READMEs")

        # Domains
        lang_set = {l.lower() for l in lang_count}
        for domain, keywords in _DOMAIN_MAP.items():
            if lang_set & keywords:
                profile.domains.append(domain)

    if linkedin:
        profile.confirmed_skills.extend(linkedin.skills)

        for exp in linkedin.experience:
            title = (exp.get("title") or "").lower()
            if any(w in title for w in ("senior", "lead", "architect", "principal", "staff")):
                profile.seniority_signals.append(f"Title: {exp.get('title')}")

        # Rough experience years from date ranges
        import re
        years: list[int] = []
        for exp in linkedin.experience:
            dates = exp.get("dates") or ""
            matches = re.findall(r"\b(20\d{2}|19\d{2})\b", dates)
            if len(matches) >= 2:
                years.extend(int(y) for y in matches)
        if years:
            profile.experience_years_estimate = max(years) - min(years)

    # Deduplicate
    profile.confirmed_skills = list(dict.fromkeys(profile.confirmed_skills))
    profile.inferred_skills = [s for s in dict.fromkeys(profile.inferred_skills)
                                if s not in profile.confirmed_skills]

    return profile
