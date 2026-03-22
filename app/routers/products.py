from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.products import get_product, get_products, get_recommended_products
from app.database import get_db
from app.schemas.product import ProductOut

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/recommended", response_model=List[ProductOut])
async def recommended(
    style: str = Query(default=""),
    limit: int = Query(default=4, le=20),
    db: AsyncSession = Depends(get_db),
):
    styles = [s.strip() for s in style.split(",") if s.strip()]
    products = await get_recommended_products(db, styles, limit)
    return [ProductOut.from_orm_full(p) for p in products]


@router.get("", response_model=List[ProductOut])
async def list_products(
    mode: str | None = Query(default=None),
    category: str | None = Query(default=None),
    brand_id: str | None = Query(default=None),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0),
    db: AsyncSession = Depends(get_db),
):
    products = await get_products(db, mode=mode, category=category, brand_id=brand_id, limit=limit, offset=offset)
    return [ProductOut.from_orm_full(p) for p in products]


@router.get("/{product_id}", response_model=ProductOut)
async def get_one(product_id: str, db: AsyncSession = Depends(get_db)):
    product = await get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductOut.from_orm_full(product)
