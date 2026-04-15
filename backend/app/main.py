import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.database import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    os.makedirs(settings.upload_dir, exist_ok=True)
    await init_db()
    yield
    # Shutdown (nothing to clean up for SQLite)


app = FastAPI(
    title="JobHunt AI",
    description="Multi-board job scraper with ATS optimizer and cover letter generator",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded files (for resume download)
os.makedirs(settings.upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# ── Routers ───────────────────────────────────────────────────────────────────
from app.api.routes import jobs, resume, generate, interview  # noqa: E402

app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(resume.router, prefix="/api/resume", tags=["Resume"])
app.include_router(generate.router, prefix="/api/generate", tags=["Generate"])
app.include_router(interview.router, prefix="/api/interview", tags=["Interview"])


@app.get("/api/health", tags=["Health"])
async def health() -> dict:
    return {"status": "ok", "env": settings.app_env}
