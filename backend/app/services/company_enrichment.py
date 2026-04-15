"""Company enrichment — DuckDuckGo + slug-based URL construction. No paid APIs."""
from __future__ import annotations

import re
from dataclasses import dataclass

import httpx


@dataclass
class CompanyLinks:
    website: str | None = None
    careers_url: str | None = None
    glassdoor_url: str | None = None
    linkedin_url: str | None = None
    indeed_url: str | None = None


def _slug(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    return re.sub(r"\s+", "-", s).strip("-")


async def enrich_company(company_name: str) -> CompanyLinks:
    slug = _slug(company_name)
    links = CompanyLinks(
        careers_url=None,
        glassdoor_url=f"https://www.glassdoor.com/Reviews/{slug}-reviews.htm",
        linkedin_url=f"https://www.linkedin.com/company/{slug}",
        indeed_url=f"https://www.indeed.com/cmp/{slug}",
    )

    try:
        encoded = company_name.replace(" ", "+")
        url = f"https://api.duckduckgo.com/?q={encoded}+official+website&format=json&no_redirect=1&no_html=1"
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            data = resp.json()
            abstract_url = data.get("AbstractURL") or ""
            if abstract_url and abstract_url.startswith("http"):
                links.website = abstract_url
    except Exception:
        pass

    return links
