from __future__ import annotations
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.outfits import (
    generate_outfit,
    get_alternatives,
    get_outfit,
    get_outfits,
    get_saved_outfit_ids,
    get_saved_outfits,
    rate_outfit,
    save_outfit,
    unsave_outfit,
)
from app.database import get_db
from app.deps import get_current_user, get_optional_user
from app.models.user import User
from app.schemas.outfit import OutfitOut
from app.schemas.product import ProductOut

router = APIRouter(prefix="/outfits", tags=["outfits"])


# ─── List precomputed outfits ─────────────────────────────────────────────────

@router.get("", response_model=List[OutfitOut])
async def list_outfits(
    scope: str | None = Query(default=None, description="'local' | 'global' | 'both'"),
    db: AsyncSession = Depends(get_db),
):
    outfits = await get_outfits(db, scope=scope)
    return [OutfitOut.from_orm_outfit(o) for o in outfits]


# ─── Saved outfit IDs (fast, for initial load) ────────────────────────────────

@router.get("/saved/ids", response_model=List[str])
async def list_saved_ids(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_saved_outfit_ids(db, current_user.id)


# ─── Saved outfits (full objects) ─────────────────────────────────────────────

@router.get("/saved", response_model=List[OutfitOut])
async def list_saved_outfits(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    outfits = await get_saved_outfits(db, current_user.id)
    return [OutfitOut.from_orm_outfit(o) for o in outfits]


# ─── Swap alternatives ────────────────────────────────────────────────────────

@router.get("/alternatives", response_model=List[ProductOut])
async def list_alternatives(
    role: str = Query(..., description="anchor|top|bottom|shoes|bag|accessory"),
    scope: str = Query("global"),
    exclude: str | None = Query(default=None, description="product_id to exclude"),
    limit: int = Query(default=6, le=12),
    db: AsyncSession = Depends(get_db),
):
    products = await get_alternatives(db, role=role, scope=scope, exclude_id=exclude, limit=limit)
    return [ProductOut.from_orm_full(p) for p in products]


# ─── Generate outfit via algorithm ───────────────────────────────────────────

class GenerateRequest(BaseModel):
    style: str = ""
    budget: str = ""      # "<300" | "300-800" | "800+"
    occasion: str = ""    # "casual" | "evening" | "work" | "weekend"
    scope: str = "global" # "local" | "global"


@router.post("/generate", response_model=OutfitOut)
async def generate(body: GenerateRequest, db: AsyncSession = Depends(get_db)):
    outfit = await generate_outfit(
        db,
        style=body.style,
        budget=body.budget,
        occasion=body.occasion,
        scope=body.scope,
    )
    if not outfit:
        raise HTTPException(
            status_code=404,
            detail="No products found matching your preferences. Try a different style or budget.",
        )
    return OutfitOut.from_orm_outfit(outfit)


# ─── Single outfit ────────────────────────────────────────────────────────────

@router.get("/{outfit_id}", response_model=OutfitOut)
async def get_one_outfit(outfit_id: str, db: AsyncSession = Depends(get_db)):
    outfit = await get_outfit(db, outfit_id)
    if not outfit:
        raise HTTPException(status_code=404, detail="Outfit not found")
    return OutfitOut.from_orm_outfit(outfit)


# ─── Save / unsave outfit ─────────────────────────────────────────────────────

@router.post("/{outfit_id}/save", status_code=204)
async def save(
    outfit_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await save_outfit(db, user_id=current_user.id, outfit_id=outfit_id)


@router.delete("/{outfit_id}/save", status_code=204)
async def unsave(
    outfit_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await unsave_outfit(db, user_id=current_user.id, outfit_id=outfit_id)


# ─── Rate outfit ─────────────────────────────────────────────────────────────

class RateRequest(BaseModel):
    rating: str  # "up" | "down"


@router.post("/{outfit_id}/rate", status_code=204)
async def rate(
    outfit_id: str,
    body: RateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.rating not in ("up", "down"):
        raise HTTPException(status_code=422, detail="rating must be 'up' or 'down'")
    await rate_outfit(db, user_id=current_user.id, outfit_id=outfit_id, rating=body.rating)
