from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.brands import get_brand, get_brand_by_slug, get_brands
from app.crud.products import get_products
from app.crud.stores import get_stores
from app.database import get_db
from app.schemas.brand import BrandOut
from app.schemas.product import ProductOut
from app.schemas.store import StoreOut

router = APIRouter(prefix="/brands", tags=["brands"])


@router.get("", response_model=List[BrandOut])
async def list_brands(db: AsyncSession = Depends(get_db)):
    brands = await get_brands(db)
    return [BrandOut.model_validate(b) for b in brands]


@router.get("/{brand_id}", response_model=dict)
async def get_one(brand_id: str, db: AsyncSession = Depends(get_db)):
    # Try by ID first, then by slug
    brand = await get_brand(db, brand_id)
    if not brand:
        brand = await get_brand_by_slug(db, brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    products = await get_products(db, brand_id=brand.id, limit=50)
    stores = await get_stores(db)
    brand_stores = [s for s in stores if s.brand_id == brand.id]

    return {
        "brand": BrandOut.model_validate(brand),
        "products": [ProductOut.from_orm_full(p) for p in products],
        "stores": [StoreOut.from_orm_full(s) for s in brand_stores],
    }
