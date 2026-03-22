from __future__ import annotations
from pydantic import BaseModel


class BrandOut(BaseModel):
    id: str
    slug: str
    name: str
    tagline: str | None = None
    description: str | None = None
    founded: str | None = None
    origin: str | None = None
    cover_url: str | None = None

    model_config = {"from_attributes": True}
