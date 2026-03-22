from __future__ import annotations

import base64
import re

import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/try-on", tags=["try-on"])

# ── Replicate classic endpoint (works for all community models) ───────────────
REPLICATE_PREDS = "https://api.replicate.com/v1/predictions"

# CatVTON-Flux — ICLR 2025 SOTA try-on, much better than IDM-VTON
# https://replicate.com/mmezhov/catvton-flux
CATVTON_VERSION = "cc41d1b963023987ed2ddf26e9264efcc96ee076640115c303f95b0010f6a958"

# Wan 2.2 i2v-fast — fast image → video (rotation animation)
# https://replicate.com/wan-video/wan-2.2-i2v-fast
WAN_I2V_VERSION = "616fe5913f5c30db10afc0576c0c1179a1d11a713273fa3ad529b0e47370b62a"

VIDEO_PROMPT = (
    "Fashion model slowly turns around to show the outfit from every angle. "
    "360 degrees full rotation, elegant editorial, soft natural lighting, "
    "smooth fluid motion, cinematic, high quality."
)

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}
MAX_BYTES = 15 * 1024 * 1024  # 15 MB
MIN_BYTES = 50 * 1024          # 50 KB


# ── Schemas ───────────────────────────────────────────────────────────────────

class GenerateResponse(BaseModel):
    prediction_id: str
    status: str


class StatusResponse(BaseModel):
    status: str          # starting | processing | succeeded | failed | canceled
    result_url: str | None = None
    error: str | None = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _auth_headers() -> dict[str, str]:
    if not settings.REPLICATE_API_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="Try-on service not configured. Set REPLICATE_API_TOKEN in server env vars.",
        )
    return {
        "Authorization": f"Token {settings.REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }


def _to_data_uri(content: bytes, mime: str) -> str:
    safe = mime if mime in ALLOWED_MIME else "image/jpeg"
    return f"data:{safe};base64,{base64.b64encode(content).decode()}"


async def _submit(version: str, input_payload: dict, timeout: float = 45.0) -> dict:
    """POST /v1/predictions with explicit version hash — works for all models."""
    async with httpx.AsyncClient(timeout=timeout) as http:
        resp = await http.post(
            REPLICATE_PREDS,
            headers=_auth_headers(),
            json={"version": version, "input": input_payload},
        )
    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=502, detail=f"Replicate error: {resp.text[:400]}")
    return resp.json()


async def _poll(prediction_id: str) -> dict:
    """GET /v1/predictions/{id}"""
    async with httpx.AsyncClient(timeout=15.0) as http:
        resp = await http.get(
            f"{REPLICATE_PREDS}/{prediction_id}",
            headers=_auth_headers(),
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Could not fetch prediction status.")
    return resp.json()


def _extract_url(data: dict) -> str | None:
    out = data.get("output")
    if not out:
        return None
    return out[0] if isinstance(out, list) else out if isinstance(out, str) else None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/generate", response_model=GenerateResponse)
async def generate_try_on(
    person_image: UploadFile = File(..., description="Full-body portrait photo"),
    garment_image_url: str = Form(..., description="Public URL of the garment image"),
):
    """
    Submit a try-on job via CatVTON-Flux (SOTA quality).
    Poll /try-on/status/{id} until succeeded.
    """
    _auth_headers()  # validate token early

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

    # CatVTON-Flux inputs: image (person), garment (clothing), try_on=True
    data = await _submit(CATVTON_VERSION, {
        "image":   person_data_uri,
        "garment": garment_image_url,
        "try_on":  True,
        "num_steps": 30,
        "guidance_scale": 2.5,
        "seed": 42,
    })

    return GenerateResponse(prediction_id=data["id"], status=data["status"])


@router.get("/status/{prediction_id}", response_model=StatusResponse)
async def get_try_on_status(prediction_id: str):
    """Poll a try-on image prediction."""
    _auth_headers()
    if not re.match(r"^[a-z0-9]{10,40}$", prediction_id):
        raise HTTPException(status_code=400, detail="Invalid prediction ID.")

    data = await _poll(prediction_id)
    status = data.get("status", "unknown")
    return StatusResponse(
        status=status,
        result_url=_extract_url(data) if status == "succeeded" else None,
        error=data.get("error") if status == "failed" else None,
    )


@router.post("/video", response_model=GenerateResponse)
async def generate_rotation_video(
    image_url: str = Form(..., description="Try-on result image URL to animate"),
):
    """
    Animate the try-on result into a short 360° rotation video via Wan 2.2 i2v.
    """
    _auth_headers()
    if not re.match(r"^https?://", image_url):
        raise HTTPException(status_code=400, detail="image_url must be a valid HTTP/S URL.")

    data = await _submit(WAN_I2V_VERSION, {
        "image":             image_url,
        "prompt":            VIDEO_PROMPT,
        "num_frames":        81,
        "frames_per_second": 16,
        "resolution":        "480p",
        "go_fast":           True,
        "sample_shift":      12,
    })

    return GenerateResponse(prediction_id=data["id"], status=data["status"])


@router.get("/video-status/{prediction_id}", response_model=StatusResponse)
async def get_video_status(prediction_id: str):
    """Poll a video generation prediction."""
    _auth_headers()
    if not re.match(r"^[a-z0-9]{10,40}$", prediction_id):
        raise HTTPException(status_code=400, detail="Invalid prediction ID.")

    data = await _poll(prediction_id)
    status = data.get("status", "unknown")
    return StatusResponse(
        status=status,
        result_url=_extract_url(data) if status == "succeeded" else None,
        error=data.get("error") if status == "failed" else None,
    )
