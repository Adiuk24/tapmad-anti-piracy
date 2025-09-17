from __future__ import annotations

import json
import os
import requests
from typing import Any

from fastapi import FastAPI, HTTPException
from ..shared.config import settings

OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
MODEL = os.getenv("LLM_MODEL", settings.llm_model)

app = FastAPI(title="LLM Sidecar")


def _ollama_generate(prompt: str, options: dict[str, Any] | None = None) -> str:
    payload = {"model": MODEL, "prompt": prompt, "stream": False}
    if options:
        payload["options"] = options
    try:
        resp = requests.post(f"{OLLAMA_BASE}/api/generate", json=payload, timeout=120)
        resp.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM backend error: {e}")
    data = resp.json()
    return data.get("response", "")


@app.post("/generate")
def generate(data: dict[str, str]) -> str:
    prompt = data.get("prompt", "")
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt required")
    return _ollama_generate(prompt)


@app.post("/expand_keywords")
def expand_keywords(data: dict[str, Any]) -> dict[str, list[str]]:
    seeds = data.get("seeds", [])
    event_meta = {k: v for k, v in (data or {}).items() if k != "seeds"}
    
    # Use hardcoded keywords for now
    # TODO: Fix LLM model training for proper JSON output
    hardcoded_keywords = [
        "tapmad live",
        "tapmad sports",
        "live cricket tapmad",
        "free match stream",
        "live match hd",
        "ট্যাপম্যাড লাইভ",
        "ফ্রি খেলা লাইভ",
        "লাইভ ম্যাচ এইচডি",
        "খেলা ফ্রি স্ট্রিম",
        "cricket live streaming",
        "football live bangla",
        "sports pirati website",
        "live tv streaming",
        "match highlights",
        "sports commentary",
        "live score",
        "match replay",
        "sports news",
        "game analysis",
        "match summary"
    ]
    
    return {"keywords": hardcoded_keywords}


@app.post("/classify_page")
def classify_page(data: dict[str, Any]) -> dict[str, Any]:
    text = (data.get("text") or "").strip()
    lang = data.get("lang") or "en"
    if not text:
        return {"label": "unrelated", "score": 0.0}
    
    # Use hardcoded classification for now
    t = text.lower()
    if any(k in t for k in ["live", "stream", "match", "watch", "খেলা", "লাইভ"]):
        return {"label": "likely_stream", "score": 0.7}
    if any(k in t for k in ["commentary", "radio", "reaction", "watchalong"]):
        return {"label": "commentary", "score": 0.6}
    return {"label": "unrelated", "score": 0.2}


@app.post("/draft_takedown")
def draft_takedown(data: dict[str, Any]) -> str:
    summary = data.get("summary", "")
    
    # Use hardcoded takedown template for now
    template = f"""
Dear Platform Team,

We have identified unauthorized distribution of Tapmad content on your platform.

Summary of Violation:
{summary}

This constitutes copyright infringement under applicable laws. We request immediate removal of this content.

Please confirm removal within 24 hours.

Regards,
Tapmad Anti-Piracy Team
"""
    return template.strip()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8089)
