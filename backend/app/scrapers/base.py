from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RawJob:
    """Normalised job record produced by any scraper."""

    title: str
    board: str
    company: str | None = None
    location: str | None = None
    description: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = "CAD"
    salary_interval: str | None = None   # yearly | monthly | hourly
    skills: list[str] = field(default_factory=list)
    seniority_level: str | None = None
    employment_type: str | None = None
    is_remote: bool = False
    job_url: str | None = None
    posted_at: datetime | None = None


class BaseScraper(abc.ABC):
    """Every board scraper must implement this interface."""

    board_name: str = "unknown"

    @abc.abstractmethod
    async def scrape(
        self,
        keywords: str,
        location: str,
        remote_only: bool = False,
        max_results: int = 25,
    ) -> list[RawJob]:
        ...
