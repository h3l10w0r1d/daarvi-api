from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.brand import Brand
from app.models.product import Product, ProductAvailability, ProductImage, ProductColor, ProductSize, ProductTag
from app.models.store import Store


async def get_brands(db: AsyncSession) -> list[Brand]:
    result = await db.execute(select(Brand).order_by(Brand.name))
    return result.scalars().all()


async def get_brand(db: AsyncSession, brand_id: str) -> Brand | None:
    result = await db.execute(
        select(Brand).where(Brand.id == brand_id)
    )
    return result.scalar_one_or_none()


async def get_brand_by_slug(db: AsyncSession, slug: str) -> Brand | None:
    result = await db.execute(
        select(Brand).where(Brand.slug == slug)
    )
    return result.scalar_one_or_none()
