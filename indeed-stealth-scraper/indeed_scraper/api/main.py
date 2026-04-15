"""
api/main.py — FastAPI application: mounts API routes and serves the UI.

Run from the project root (indeed-stealth-scraper/):
    python -m indeed_scraper.api.main
    -- or --
    python indeed_scraper/api/main.py
"""

import sys
from pathlib import Path

# Ensure the project root is importable when run directly
_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from indeed_scraper.api.routes.export import router as export_router
from indeed_scraper.api.routes.results import router as results_router
from indeed_scraper.api.routes.scrape import router as scrape_router

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Indeed Scraper UI",
    description="Local web interface for the Indeed Canada stealth scraper.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*", "http://127.0.0.1:*"],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# API routes  (must be registered BEFORE the static file catch-all)
# ---------------------------------------------------------------------------

app.include_router(scrape_router, prefix="/api", tags=["Scrape"])
app.include_router(results_router, prefix="/api", tags=["Results"])
app.include_router(export_router, prefix="/api", tags=["Export"])

# ---------------------------------------------------------------------------
# Serve the UI (index.html + app.js + style.css)
# ---------------------------------------------------------------------------

_UI_DIR = Path(__file__).parent.parent / "ui"

if _UI_DIR.exists():
    app.mount("/", StaticFiles(directory=str(_UI_DIR), html=True), name="ui")
else:
    import warnings
    warnings.warn(f"UI directory not found: {_UI_DIR}")

# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "indeed_scraper.api.main:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info",
    )
