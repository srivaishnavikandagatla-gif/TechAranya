"""FastAPI server: serves the web UI and the /api/diagnose endpoint."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()  # must run before importing diagnose (which creates the client)

import anthropic  # noqa: E402
from fastapi import FastAPI, File, Form, HTTPException, UploadFile  # noqa: E402
from fastapi.concurrency import run_in_threadpool  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from .diagnose import Diagnosis, DiagnosisError, diagnose_plant  # noqa: E402

log = logging.getLogger("plant")

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_IMAGES = 3
MAX_BYTES = 5 * 1024 * 1024  # per image (Claude's per-image limit)

app = FastAPI(title="TechAranya - AI Plant Doctor")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/diagnose", response_model=Diagnosis)
async def diagnose(
    images: List[UploadFile] = File(...),
    plant_name: str = Form(""),
    location: str = Form("Garden"),
    language: str = Form("English"),
    pot_or_ground: str = Form(""),
    watering: str = Form(""),
    notes: str = Form(""),
    organic_only: Optional[bool] = Form(False),
):
    if not images:
        raise HTTPException(400, "Please add at least one photo.")
    if len(images) > MAX_IMAGES:
        raise HTTPException(400, f"Please upload at most {MAX_IMAGES} photos.")

    payload = []
    for img in images:
        if img.content_type not in ALLOWED_TYPES:
            raise HTTPException(400, f"Unsupported image type: {img.content_type}")
        data = await img.read()
        if len(data) > MAX_BYTES:
            raise HTTPException(400, "Each photo must be under 5 MB.")
        payload.append((data, img.content_type))

    try:
        return await run_in_threadpool(
            diagnose_plant,
            payload,
            plant_name=plant_name.strip()[:100],
            location=location.strip()[:50],
            language=language.strip()[:30],
            pot_or_ground=pot_or_ground.strip()[:30],
            watering=watering.strip()[:100],
            notes=notes.strip()[:500],
            organic_only=bool(organic_only),
        )
    except DiagnosisError as e:
        raise HTTPException(422, str(e))
    except anthropic.AuthenticationError:
        raise HTTPException(500, "Server API key is missing or invalid.")
    except anthropic.RateLimitError:
        raise HTTPException(429, "Too many requests right now - please retry in a moment.")
    except anthropic.APIStatusError as e:
        log.exception("Claude API error")
        raise HTTPException(502, f"AI service error ({e.status_code}). Please try again.")
    except anthropic.APIConnectionError:
        raise HTTPException(503, "Could not reach the AI service. Check your connection.")
    except TypeError as e:
        if "authentication" in str(e):  # no API key configured
            raise HTTPException(500, "Server has no ANTHROPIC_API_KEY set. Add it to .env and restart.")
        log.exception("Unexpected error")
        raise HTTPException(500, "Unexpected server error. Please try again.")
