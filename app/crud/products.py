from __future__ import annotations
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Product, ProductTag


async def get_products(
    db: AsyncSession,
    mode: str | None = None,
    category: str | None = None,
    brand_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Product]:
    from app.models.product import ProductAvailability

    stmt = select(Product).options(
        selectinload(Product.brand),
        selectinload(Product.images),
        selectinload(Product.colors),
        selectinload(Product.sizes),
        selectinload(Product.tags),
        selectinload(Product.availability),
    )

    if mode:
        stmt = stmt.join(ProductAvailability, ProductAvailability.product_id == Product.id).where(
            ProductAvailability.mode == mode
        )
    if category:
        stmt = stmt.where(Product.category == category)
    if brand_id:
        stmt = stmt.where(Product.brand_id == brand_id)

    stmt = stmt.offset(offset).limit(limit).distinct()
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_product(db: AsyncSession, product_id: str) -> Product | None:
    stmt = select(Product).where(Product.id == product_id).options(
        selectinload(Product.brand),
        selectinload(Product.images),
        selectinload(Product.colors),
        selectinload(Product.sizes),
        selectinload(Product.tags),
        selectinload(Product.availability),
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_recommended_products(
    db: AsyncSession,
    styles: list[str],
    limit: int = 4,
) -> list[Product]:
    if not styles:
        return []

    stmt = (
        select(Product)
        .join(ProductTag, ProductTag.product_id == Product.id)
        .where(ProductTag.tag.in_(styles))
        .options(
            selectinload(Product.brand),
            selectinload(Product.images),
            selectinload(Product.colors),
            selectinload(Product.sizes),
            selectinload(Product.tags),
            selectinload(Product.availability),
        )
        .distinct()
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()
