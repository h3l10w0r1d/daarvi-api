from __future__ import annotations
import json
from pydantic import BaseModel

from app.schemas.product import ProductOut


class OutfitItemOut(BaseModel):
    role: str
    is_core: bool
    product: ProductOut

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_item(cls, item) -> "OutfitItemOut":
        return cls(
            role=item.role,
            is_core=item.is_core,
            product=ProductOut.from_orm_full(item.product),
        )


class OutfitOut(BaseModel):
    id: str
    title: str
    description: str | None = None
    scope: str
    occasion: str | None = None
    style_tags: list[str] = []
    hero_image: str | None = None
    anchor_id: str | None = None
    items: list[OutfitItemOut] = []

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_outfit(cls, o) -> "OutfitOut":
        try:
            tags = json.loads(o.style_tags) if o.style_tags else []
        except (ValueError, TypeError):
            tags = []
        return cls(
            id=o.id,
            title=o.title,
            description=o.description,
            scope=o.scope,
            occasion=o.occasion,
            style_tags=tags,
            hero_image=getattr(o, "hero_image", None),
            anchor_id=o.anchor_id,
            items=[OutfitItemOut.from_orm_item(i) for i in o.items],
        )
