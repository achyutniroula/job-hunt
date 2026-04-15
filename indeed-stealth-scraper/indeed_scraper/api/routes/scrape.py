"""
routes/scrape.py — POST /api/scrape, DELETE /api/scrape/stop, GET /api/scrape/status
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from indeed_scraper.api.scrape_runner import get_state_snapshot, start_scrape, stop_scrape

router = APIRouter()


class ScrapeRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Job search keyword(s)")
    location: str = Field(..., min_length=1, description="Location (e.g. Toronto, ON)")
    pages: int = Field(default=10, ge=1, le=20, description="Max pages to scrape")
    output_dir: str = Field(default="output", description="Directory for saved files")
    resume: bool = Field(default=False, description="Continue from last offset (Get More Jobs)")


@router.post("/scrape")
async def start_scrape_endpoint(body: ScrapeRequest) -> dict:
    """Start a background scrape session."""
    started = start_scrape(
        query=body.query,
        location=body.location,
        pages=body.pages,
        output_dir=body.output_dir,
        resume=body.resume,
    )
    if not started:
        raise HTTPException(status_code=409, detail="A scrape is already running.")
    return {"status": "started", "query": body.query, "location": body.location}


@router.delete("/scrape/stop")
async def stop_scrape_endpoint() -> dict:
    """Signal the running scrape to stop."""
    stop_scrape()
    return {"status": "stop_requested"}


@router.get("/scrape/status")
async def scrape_status() -> dict:
    """Return the current scrape state (status, counters, recent logs)."""
    return get_state_snapshot()
