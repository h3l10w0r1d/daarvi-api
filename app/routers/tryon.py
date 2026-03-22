from __future__ import annotations

import base64
import re

import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/try-on", tags=["try-on"])

REPLICATE_API_URL = "https://api.replicate.com/v1/predictions"
# IDM-VTON — high-fidelity virtual clothing try-on
VTON_MODEL_VERSION = "c871bb9b046607b680449ecbae55fd8c6d945e0a1948644bf2361b3d021d3ff4"

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_BYTES = 15 * 1024 * 1024  # 15 MB
MIN_BYTES = 50 * 1024          # 50 KB


# ── Schemas ──────────────────────────────────────────────────────────────────

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
            detail="Try-on service is not configured. Add REPLICATE_API_TOKEN to server env vars.",
        )
    return {
        "Authorization": f"Token {settings.REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }


def _to_data_uri(content: bytes, mime: str) -> str:
    safe_mime = mime if mime in ALLOWED_MIME_TYPES else "image/jpeg"
    return f"data:{safe_mime};base64,{base64.b64encode(content).decode()}"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/generate", response_model=GenerateResponse)
async def generate_try_on(
    person_image: UploadFile = File(..., description="Full-body portrait photo of the person"),
    garment_image_url: str = Form(..., description="Public URL of the garment product image"),
    garment_description: str = Form("fashion garment", description="Short text describing the garment"),
):
    """
    Submit a virtual try-on job to Replicate.
    Returns a prediction_id; poll /try-on/status/{id} until succeeded/failed.
    """
    headers = _auth_headers()

    # ── Validate upload ──
    mime = person_image.content_type or "image/jpeg"
    if mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported image format. Use JPG, PNG, or WebP.")

    img_bytes = await person_image.read()

    if len(img_bytes) < MIN_BYTES:
        raise HTTPException(status_code=400, detail="Image too small — please upload a high-quality full-body photo.")
    if len(img_bytes) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="Image exceeds 15 MB limit.")

    # ── Validate garment URL ──
    if not re.match(r"^https?://", garment_image_url):
        raise HTTPException(status_code=400, detail="garment_image_url must be a valid HTTP/S URL.")

    person_data_uri = _to_data_uri(img_bytes, mime)

    # ── Submit to Replicate ──
    payload = {
        "version": VTON_MODEL_VERSION,
        "input": {
            "human_img": person_data_uri,
            "garm_img": garment_image_url,
            "garment_des": garment_description[:120],
            "is_checked": True,
            "is_checked_crop": False,
            "denoise_steps": 30,
            "seed": 42,
        },
    }

    async with httpx.AsyncClient(timeout=45.0) as http:
        resp = await http.post(REPLICATE_API_URL, headers=headers, json=payload)

    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=502, detail=f"Replicate submission failed: {resp.text[:400]}")

    data = resp.json()
    return GenerateResponse(prediction_id=data["id"], status=data["status"])


@router.get("/status/{prediction_id}", response_model=StatusResponse)
async def get_try_on_status(prediction_id: str):
    """Poll the status of a try-on prediction."""
    headers = _auth_headers()

    # Basic sanity check on the prediction ID
    if not re.match(r"^[a-z0-9]{20,30}$", prediction_id):
        raise HTTPException(status_code=400, detail="Invalid prediction ID.")

    async with httpx.AsyncClient(timeout=15.0) as http:
        resp = await http.get(
            f"{REPLICATE_API_URL}/{prediction_id}",
            headers=headers,
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Could not fetch prediction status from Replicate.")

    data = resp.json()
    status = data.get("status", "unknown")

    result_url: str | None = None
    if status == "succeeded":
        output = data.get("output")
        if isinstance(output, list) and output:
            result_url = output[0]
        elif isinstance(output, str):
            result_url = output

    error = data.get("error") if status == "failed" else None

    return StatusResponse(status=status, result_url=result_url, error=error)
