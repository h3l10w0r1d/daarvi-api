from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.users import (
    add_to_wishlist,
    get_wishlist_product_ids,
    remove_from_wishlist,
    update_user_name,
    upsert_dna_profile,
)
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.user import DnaProfileIn, DnaProfileOut, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserOut.from_orm_full(current_user)


@router.put("/me", response_model=UserOut)
async def update_me(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.name:
        await update_user_name(db, current_user, body.name)
    # Re-fetch with relationships
    from app.crud.users import get_user_by_id
    updated = await get_user_by_id(db, current_user.id)
    return UserOut.from_orm_full(updated)


@router.post("/me/dna-profile", response_model=DnaProfileOut)
async def save_dna_profile(
    body: DnaProfileIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await upsert_dna_profile(db, current_user, body.model_dump())
    from app.models.user import DnaProfile, DnaStylePreference
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(DnaProfile).where(DnaProfile.id == profile.id).options(selectinload(DnaProfile.style_preferences))
    )
    profile = result.scalar_one()
    return DnaProfileOut(
        shape=profile.shape,
        style=[sp.style for sp in profile.style_preferences],
        palette=profile.palette,
        budget=profile.budget,
        mode=profile.mode,
    )


@router.get("/me/dna-profile", response_model=Optional[DnaProfileOut])
async def get_dna_profile(current_user: User = Depends(get_current_user)):
    if not current_user.dna_profile:
        return None
    return DnaProfileOut(
        shape=current_user.dna_profile.shape,
        style=[sp.style for sp in current_user.dna_profile.style_preferences],
        palette=current_user.dna_profile.palette,
        budget=current_user.dna_profile.budget,
        mode=current_user.dna_profile.mode,
    )


@router.get("/me/wishlist", response_model=List[str])
async def get_wishlist(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_wishlist_product_ids(db, current_user.id)


@router.post("/me/wishlist/{product_id}", status_code=204)
async def add_wishlist(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await add_to_wishlist(db, current_user.id, product_id)


@router.delete("/me/wishlist/{product_id}", status_code=204)
async def remove_wishlist(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await remove_from_wishlist(db, current_user.id, product_id)
