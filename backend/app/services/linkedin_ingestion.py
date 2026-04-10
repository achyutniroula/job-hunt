from __future__ import annotations

import logging
from dataclasses import dataclass, field

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass
class LinkedInProfile:
    name: str | None = None
    headline: str | None = None
    location: str | None = None
    experience: list[dict] = field(default_factory=list)
    education: list[dict] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    linkedin_unavailable: bool = False


def _is_blocked(url: str, body: str) -> bool:
    url_l = url.lower()
    return "authwall" in url_l or "login" in url_l or "authwall" in body[:2000] or "Sign in" in body[:500]


async def fetch_linkedin_profile(url: str) -> LinkedInProfile:
    try:
        async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True, timeout=15.0) as client:
            resp = await client.get(url)
            if resp.status_code != 200 or _is_blocked(str(resp.url), resp.text):
                logger.info("LinkedIn blocked or unavailable for %s", url)
                return LinkedInProfile(linkedin_unavailable=True)

        soup = BeautifulSoup(resp.text, "lxml")

        name = _text(soup, ["h1.top-card-layout__title", "h1.text-heading-xlarge", "h1"])
        headline = _text(soup, [".top-card-layout__headline", ".text-body-medium"])
        location = _text(soup, [".top-card__subline-item", ".top-card-layout__first-subline"])

        experience: list[dict] = []
        for item in soup.select(".experience-item, .position-group-pager li, [data-section='experience'] li")[:8]:
            title = _text(item, ["h3", ".experience-item__title", ".mr1.t-bold span"])
            company = _text(item, [".experience-item__subtitle", ".t-14.t-normal span"])
            dates = _text(item, [".experience-item__duration", ".t-14.t-normal.t-black--light span"])
            if title:
                experience.append({"title": title, "company": company, "dates": dates})

        education: list[dict] = []
        for item in soup.select(".education__item, [data-section='education'] li")[:4]:
            school = _text(item, ["h3", ".education__item--degree-info h3"])
            degree = _text(item, [".education__item--degree-info span", ".t-14.t-normal"])
            if school:
                education.append({"school": school, "degree": degree})

        skills: list[str] = []
        for el in soup.select(".skills-section li, .pv-skill-category-entity__name, [data-section='skills'] li")[:30]:
            t = el.get_text(strip=True)
            if t:
                skills.append(t)

        return LinkedInProfile(
            name=name, headline=headline, location=location,
            experience=experience, education=education, skills=skills,
            linkedin_unavailable=False,
        )
    except Exception as exc:
        logger.warning("LinkedIn ingestion failed: %s", exc)
        return LinkedInProfile(linkedin_unavailable=True)


def _text(el, selectors: list[str]) -> str | None:
    for sel in selectors:
        found = el.select_one(sel) if hasattr(el, "select_one") else None
        if found:
            t = found.get_text(strip=True)
            if t:
                return t
    return None
