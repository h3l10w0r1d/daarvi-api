from __future__ import annotations
from pydantic import BaseModel

from app.schemas.brand import BrandOut


class StoreOut(BaseModel):
    id: str
    name: str
    brand_id: str
    brand: BrandOut | None = None
    type: str
    lat: float
    lng: float
    city: str
    distance: str | None = None
    product_ids: list[str] = []

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_full(cls, s) -> "StoreOut":
        return cls(
            id=s.id,
            name=s.name,
            brand_id=s.brand_id,
            brand=BrandOut.model_validate(s.brand) if s.brand else None,
            type=s.type,
            lat=s.lat,
            lng=s.lng,
            city=s.city,
            distance=s.distance,
            product_ids=[sp.product_id for sp in s.product_links],
        )
