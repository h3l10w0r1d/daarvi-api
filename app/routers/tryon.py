from __future__ import annotations

import base64
import re

import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/try-on", tags=["try-on"])

# ── FASHN AI — virtual try-on ─────────────────────────────────────────────────
FASHN_BASE   = "https://api.fashn.ai/v1"
FASHN_RUN    = f"{FASHN_BASE}/run"
FASHN_STATUS = f"{FASHN_BASE}/status"   # + /{prediction_id}

# ── Replicate — rotation video (Wan 2.2 i2v) ─────────────────────────────────
REPLICATE_PREDS  = "https://api.replicate.com/v1/predictions"
WAN_I2V_VERSION  = "616fe5913f5c30db10afc0576c0c1179a1d11a713273fa3ad529b0e47370b62a"

VIDEO_PROMPT = (
    "Fashion model slowly turns around to show the outfit from every angle. "
    "360 degrees full rotation, elegant editorial, soft natural lighting, "
    "smooth fluid motion, cinematic, high quality."
)

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}
MAX_BYTES    = 15 * 1024 * 1024   # 15 MB
MIN_BYTES    = 50 * 1024           # 50 KB


# ── Schemas ───────────────────────────────────────────────────────────────────

class GenerateResponse(BaseModel):
    prediction_id: str
    status: str

class StatusResponse(BaseModel):
    status: str          # processing | succeeded | failed
    result_url: str | None = None
    error: str | None = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fashn_headers() -> dict[str, str]:
    if not settings.FASHN_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Try-on service not configured. Add FASHN_API_KEY to server env vars.",
        )
    return {
        "Authorization": f"Bearer {settings.FASHN_API_KEY}",
        "Content-Type": "application/json",
    }

def _replicate_headers() -> dict[str, str]:
    if not settings.REPLICATE_API_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="Video service not configured. Add REPLICATE_API_TOKEN to server env vars.",
        )
    return {
        "Authorization": f"Token {settings.REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }

def _to_data_uri(content: bytes, mime: str) -> str:
    safe = mime if mime in ALLOWED_MIME else "image/jpeg"
    return f"data:{safe};base64,{base64.b64encode(content).decode()}"

def _extract_replicate_url(data: dict) -> str | None:
    out = data.get("output")
    if isinstance(out, list) and out:
        return out[0]
    if isinstance(out, str):
        return out
    return None

# Map FASHN status → our standard status labels
def _normalise_fashn_status(fashn_status: str) -> str:
    if fashn_status == "completed":
        return "succeeded"
    if fashn_status in ("starting", "in_queue", "processing"):
        return "processing"
    return fashn_status   # "failed" or unknown


# ── Try-on: generate ──────────────────────────────────────────────────────────

@router.post("/generate", response_model=GenerateResponse)
async def generate_try_on(
    person_image: UploadFile = File(..., description="Full-body portrait photo"),
    garment_image_url: str   = Form(..., description="Public URL of the garment image"),
):
    """
    Submit a try-on via FASHN AI (tryon-v1.6).
    Returns prediction_id — poll /try-on/status/{id} until succeeded.
    """
    _fashn_headers()   # validate key early

    mime = person_image.content_type or "image/jpeg"
    if mime not in ALLOWED_MIME:
        raise HTTPException(status_code=400, detail="Unsupported format. Use JPG, PNG, or WebP.")

    img_bytes = await person_image.read()
    if len(img_bytes) < MIN_BYTES:
        raise HTTPException(status_code=400, detail="Image too small — upload a high-quality full-body photo.")
    if len(img_bytes) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="Image exceeds 15 MB limit.")

    if not re.match(r"^https?://", garment_image_url):
        raise HTTPException(status_code=400, detail="garment_image_url must be a valid HTTP/S URL.")

    person_data_uri = _to_data_uri(img_bytes, mime)

    async with httpx.AsyncClient(timeout=30.0) as http:
        resp = await http.post(
            FASHN_RUN,
            headers=_fashn_headers(),
            json={
                "model_name": "tryon-v1.6",
                "inputs": {
                    "model_image":        person_data_uri,
                    "garment_image":      garment_image_url,
                    "category":           "auto",
                    "mode":               "quality",
                    "garment_photo_type": "auto",
                    "segmentation_free":  True,
                    "output_format":      "jpeg",
                    "num_samples":        1,
                    "seed":               42,
                },
            },
        )

    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=502, detail=f"FASHN error: {resp.text[:400]}")

    data = resp.json()
    return GenerateResponse(
        prediction_id=data["id"],
        status=_normalise_fashn_status(data.get("status", "processing")),
    )


# ── Try-on: poll status ───────────────────────────────────────────────────────

@router.get("/status/{prediction_id}", response_model=StatusResponse)
async def get_try_on_status(prediction_id: str):
    """Poll a FASHN try-on prediction."""
    _fashn_headers()

    async with httpx.AsyncClient(timeout=15.0) as http:
        resp = await http.get(
            f"{FASHN_STATUS}/{prediction_id}",
            headers=_fashn_headers(),
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Could not fetch prediction status from FASHN.")

    data       = resp.json()
    raw_status = data.get("status", "processing")
    status     = _normalise_fashn_status(raw_status)

    result_url: str | None = None
    if status == "succeeded":
        out = data.get("output")
        if isinstance(out, list) and out:
            result_url = out[0]
        elif isinstance(out, str):
            result_url = out

    return StatusResponse(
        status=status,
        result_url=result_url,
        error=data.get("error") if status == "failed" else None,
    )


# ── Video: generate (Replicate Wan 2.2 i2v) ──────────────────────────────────

@router.post("/video", response_model=GenerateResponse)
async def generate_rotation_video(
    image_url: str = Form(..., description="Try-on result image URL to animate"),
):
    """
    Animate the try-on result image into a 360° rotation video via Wan 2.2 i2v.
    This endpoint uses Replicate (separate REPLICATE_API_TOKEN required).
    """
    _replicate_headers()

    if not re.match(r"^https?://", image_url):
        raise HTTPException(status_code=400, detail="image_url must be a valid HTTP/S URL.")

    async with httpx.AsyncClient(timeout=45.0) as http:
        resp = await http.post(
            REPLICATE_PREDS,
            headers=_replicate_headers(),
            json={
                "version": WAN_I2V_VERSION,
                "input": {
                    "image":             image_url,
                    "prompt":            VIDEO_PROMPT,
                    "num_frames":        81,
                    "frames_per_second": 16,
                    "resolution":        "480p",
                    "go_fast":           True,
                    "sample_shift":      12,
                },
            },
        )

    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=502, detail=f"Replicate error: {resp.text[:400]}")

    data = resp.json()
    return GenerateResponse(prediction_id=data["id"], status=data["status"])


# ── Video: poll status ────────────────────────────────────────────────────────

@router.get("/video-status/{prediction_id}", response_model=StatusResponse)
async def get_video_status(prediction_id: str):
    """Poll a Replicate video prediction."""
    _replicate_headers()

    async with httpx.AsyncClient(timeout=15.0) as http:
        resp = await http.get(
            f"{REPLICATE_PREDS}/{prediction_id}",
            headers=_replicate_headers(),
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Could not fetch video status from Replicate.")

    data   = resp.json()
    status = data.get("status", "unknown")

    return StatusResponse(
        status="succeeded" if status == "succeeded" else
               "processing" if status in ("starting", "processing") else
               status,
        result_url=_extract_replicate_url(data) if status == "succeeded" else None,
        error=data.get("error") if status == "failed" else None,
    )
