from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.store import Store, StoreProduct


async def get_stores(db: AsyncSession, mode: str | None = None) -> list[Store]:
    stmt = select(Store).options(
        selectinload(Store.brand),
        selectinload(Store.product_links),
    )
    if mode:
        stmt = stmt.where(Store.type == mode)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_store(db: AsyncSession, store_id: str) -> Store | None:
    result = await db.execute(
        select(Store).where(Store.id == store_id).options(
            selectinload(Store.brand),
            selectinload(Store.product_links),
        )
    )
    return result.scalar_one_or_none()
