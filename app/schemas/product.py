from __future__ import annotations
from pydantic import BaseModel

from app.schemas.brand import BrandOut


class ProductColorOut(BaseModel):
    name: str
    hex: str
    model_config = {"from_attributes": True}


class ProductImageOut(BaseModel):
    url: str
    position: int
    model_config = {"from_attributes": True}


class ProductOut(BaseModel):
    id: str
    name: str
    brand_id: str
    brand: BrandOut | None = None
    category: str
    price_global: float
    price_local: float
    delivery_global: str | None = None
    delivery_local: str | None = None
    material: str | None = None
    fit: str | None = None
    images: list[ProductImageOut] = []
    colors: list[ProductColorOut] = []
    sizes: list[str] = []
    tags: list[str] = []
    available: list[str] = []

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_full(cls, p) -> "ProductOut":
        return cls(
            id=p.id,
            name=p.name,
            brand_id=p.brand_id,
            brand=BrandOut.model_validate(p.brand) if p.brand else None,
            category=p.category,
            price_global=float(p.price_global),
            price_local=float(p.price_local),
            delivery_global=p.delivery_global,
            delivery_local=p.delivery_local,
            material=p.material,
            fit=p.fit,
            images=[ProductImageOut.model_validate(i) for i in p.images],
            colors=[ProductColorOut.model_validate(c) for c in p.colors],
            sizes=[s.size for s in p.sizes],
            tags=[t.tag for t in p.tags],
            available=[a.mode for a in p.availability],
        )
