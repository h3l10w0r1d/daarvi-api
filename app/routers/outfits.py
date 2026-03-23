from __future__ import annotations
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.outfits import generate_outfit, get_outfit, get_outfits
from app.database import get_db
from app.schemas.outfit import OutfitOut

router = APIRouter(prefix="/outfits", tags=["outfits"])


# ─── List precomputed outfits ─────────────────────────────────────────────────

@router.get("", response_model=List[OutfitOut])
async def list_outfits(
    scope: str | None = Query(default=None, description="'local' | 'global' | 'both'"),
    db: AsyncSession = Depends(get_db),
):
    outfits = await get_outfits(db, scope=scope)
    return [OutfitOut.from_orm_outfit(o) for o in outfits]


# ─── Single outfit ────────────────────────────────────────────────────────────

@router.get("/{outfit_id}", response_model=OutfitOut)
async def get_one_outfit(outfit_id: str, db: AsyncSession = Depends(get_db)):
    outfit = await get_outfit(db, outfit_id)
    if not outfit:
        raise HTTPException(status_code=404, detail="Outfit not found")
    return OutfitOut.from_orm_outfit(outfit)


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
