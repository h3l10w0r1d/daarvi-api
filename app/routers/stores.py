from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.stores import get_stores
from app.database import get_db
from app.schemas.store import StoreOut

router = APIRouter(prefix="/stores", tags=["stores"])


@router.get("", response_model=List[StoreOut])
async def list_stores(
    mode: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    stores = await get_stores(db, mode=mode)
    return [StoreOut.from_orm_full(s) for s in stores]
