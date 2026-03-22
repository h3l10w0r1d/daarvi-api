from __future__ import annotations
from datetime import datetime

from pydantic import BaseModel


class OrderItemIn(BaseModel):
    product_id: str
    size: str | None = None
    color: str | None = None
    qty: int = 1
    price: float


class OrderIn(BaseModel):
    mode: str  # 'global' | 'local'
    items: list[OrderItemIn]
    shipping_name: str | None = None
    shipping_address: str | None = None
    shipping_city: str | None = None
    shipping_country: str | None = None


class OrderItemOut(BaseModel):
    product_id: str
    size: str | None = None
    color: str | None = None
    qty: int
    price: float

    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: str
    status: str
    mode: str
    total: float
    shipping_name: str | None = None
    shipping_address: str | None = None
    shipping_city: str | None = None
    shipping_country: str | None = None
    created_at: datetime
    items: list[OrderItemOut] = []

    model_config = {"from_attributes": True}
