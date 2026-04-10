"""
Resume API routes.

POST /api/resume/upload  — upload + parse a resume file
GET  /api/resume/{filename}/parsed — return parsed data for a stored resume
"""
from __future__ import annotations

import logging
import os

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse

from app.core.config import get_settings
from app.schemas.resume import ParsedResume, ResumeUploadResponse
from app.services.resume_parser import parse_resume

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    """
    Accept a resume file, save it, and return the parsed structured data.
    Supported formats: PDF, DOCX, TXT.
    """
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            400,
            f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    file_bytes = await file.read()

    if len(file_bytes) > settings.max_upload_bytes:
        raise HTTPException(
            413,
            f"File too large. Maximum size is {settings.max_upload_size_mb} MB.",
        )

    # Save to disk
    safe_filename = _sanitize_filename(file.filename or "resume" + ext)
    save_path = os.path.join(settings.upload_dir, safe_filename)
    os.makedirs(settings.upload_dir, exist_ok=True)
    with open(save_path, "wb") as f:
        f.write(file_bytes)

    # Parse
    try:
        parsed = parse_resume(file_bytes, safe_filename)
    except ValueError as exc:
        raise HTTPException(422, str(exc))

    return ResumeUploadResponse(filename=safe_filename, parsed=parsed)


@router.get("/{filename}/parsed", response_model=ParsedResume)
async def get_parsed_resume(filename: str):
    """Return parsed data for a previously uploaded resume."""
    safe_filename = _sanitize_filename(filename)
    path = os.path.join(settings.upload_dir, safe_filename)

    if not os.path.exists(path):
        raise HTTPException(404, "Resume not found")

    with open(path, "rb") as f:
        file_bytes = f.read()

    try:
        return parse_resume(file_bytes, safe_filename)
    except ValueError as exc:
        raise HTTPException(422, str(exc))


@router.get("/{filename}/download")
async def download_resume(filename: str):
    """Download a stored resume file."""
    safe_filename = _sanitize_filename(filename)
    path = os.path.join(settings.upload_dir, safe_filename)
    if not os.path.exists(path):
        raise HTTPException(404, "File not found")
    return FileResponse(path, filename=safe_filename)


# ── helpers ───────────────────────────────────────────────────────────────────

def _sanitize_filename(filename: str) -> str:
    """Strip path traversal characters, keep only safe filename."""
    import re
    basename = os.path.basename(filename)
    # Allow alphanumeric, dots, dashes, underscores, spaces
    safe = re.sub(r"[^\w\s.\-]", "_", basename)
    return safe[:200]
