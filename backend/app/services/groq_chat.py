"""Groq chat service — llama-3.3-70b-versatile."""
from __future__ import annotations

import httpx
from fastapi import HTTPException

from app.core.config import get_settings

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
_MODEL = "llama-3.3-70b-versatile"


async def groq_chat(messages: list[dict], max_tokens: int = 512) -> str:
    api_key = get_settings().groq_api_key
    if not api_key:
        raise HTTPException(503, "GROQ_API_KEY not configured.")

    payload = {
        "model": _MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            _GROQ_URL,
            json=payload,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        )

    if resp.status_code != 200:
        raise HTTPException(resp.status_code, f"Groq error: {resp.text[:300]}")

    return resp.json()["choices"][0]["message"]["content"]
