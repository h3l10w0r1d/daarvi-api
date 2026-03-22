from __future__ import annotations

import base64
import re

import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/try-on", tags=["try-on"])

# ── Replicate endpoints ────────────────────────────────────────────────────────
# New "run any model" endpoint — no version hash required
REPLICATE_MODELS = "https://api.replicate.com/v1/models"
REPLICATE_PREDS  = "https://api.replicate.com/v1/predictions"

# CatVTON-Flux: ICLR 2025 SOTA virtual try-on (better quality than IDM-VTON)
CATVTON_MODEL = "mmezhov/catvton-flux"

# Wan 2.2 i2v-fast: fast image → short video (rotate/animate the try-on result)
WAN_I2V_MODEL = "wan-video/wan-2.2-i2v-fast"

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


async def _submit_prediction(model_path: str, input_payload: dict, timeout: float = 45.0) -> dict:
    """POST to /v1/models/{owner}/{name}/predictions (no version hash needed)."""
    url = f"{REPLICATE_MODELS}/{model_path}/predictions"
    async with httpx.AsyncClient(timeout=timeout) as http:
        resp = await http.post(url, headers=_auth_headers(), json={"input": input_payload})
    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=502, detail=f"Replicate error: {resp.text[:400]}")
    return resp.json()


async def _poll_prediction(prediction_id: str) -> dict:
    """GET /v1/predictions/{id}"""
    async with httpx.AsyncClient(timeout=15.0) as http:
        resp = await http.get(
            f"{REPLICATE_PREDS}/{prediction_id}",
            headers=_auth_headers(),
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Could not fetch prediction status.")
    return resp.json()


def _extract_output_url(data: dict) -> str | None:
    output = data.get("output")
    if not output:
        return None
    if isinstance(output, list) and output:
        return output[0]
    if isinstance(output, str):
        return output
    return None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/generate", response_model=GenerateResponse)
async def generate_try_on(
    person_image: UploadFile = File(..., description="Full-body portrait photo"),
    garment_image_url: str = Form(..., description="Public URL of the garment image"),
):
    """
    Submit a virtual try-on job using CatVTON-Flux (SOTA quality).
    Returns prediction_id — poll /try-on/status/{id} until succeeded.
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

    # CatVTON-Flux input schema
    data = await _submit_prediction(CATVTON_MODEL, {
        "human_image": person_data_uri,
        "cloth_image":  garment_image_url,
    })

    return GenerateResponse(prediction_id=data["id"], status=data["status"])


@router.get("/status/{prediction_id}", response_model=StatusResponse)
async def get_try_on_status(prediction_id: str):
    """Poll a try-on (image) prediction status."""
    _auth_headers()

    if not re.match(r"^[a-z0-9]{10,40}$", prediction_id):
        raise HTTPException(status_code=400, detail="Invalid prediction ID.")

    data = _poll_prediction.__wrapped__(prediction_id) if hasattr(_poll_prediction, '__wrapped__') else None
    data = await _poll_prediction(prediction_id)

    status = data.get("status", "unknown")
    result_url = _extract_output_url(data) if status == "succeeded" else None
    error = data.get("error") if status == "failed" else None

    return StatusResponse(status=status, result_url=result_url, error=error)


@router.post("/video", response_model=GenerateResponse)
async def generate_rotation_video(
    image_url: str = Form(..., description="Try-on result image URL to animate"),
):
    """
    Animate a try-on result into a short rotation video using Wan 2.2 i2v.
    Feed the result URL from /try-on/status into this endpoint.
    """
    _auth_headers()

    if not re.match(r"^https?://", image_url):
        raise HTTPException(status_code=400, detail="image_url must be a valid HTTP/S URL.")

    data = await _submit_prediction(WAN_I2V_MODEL, {
        "image":             image_url,
        "prompt":            VIDEO_PROMPT,
        "num_frames":        81,        # ~5 seconds at 16 fps
        "frames_per_second": 16,
        "resolution":        "480p",
        "go_fast":           True,
        "sample_shift":      8,         # moderate motion intensity
    })

    return GenerateResponse(prediction_id=data["id"], status=data["status"])


@router.get("/video-status/{prediction_id}", response_model=StatusResponse)
async def get_video_status(prediction_id: str):
    """Poll a video generation prediction status."""
    _auth_headers()

    if not re.match(r"^[a-z0-9]{10,40}$", prediction_id):
        raise HTTPException(status_code=400, detail="Invalid prediction ID.")

    data = await _poll_prediction(prediction_id)

    status = data.get("status", "unknown")
    result_url = _extract_output_url(data) if status == "succeeded" else None
    error = data.get("error") if status == "failed" else None

    return StatusResponse(status=status, result_url=result_url, error=error)
