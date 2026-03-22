from __future__ import annotations
import uuid
from typing import List, Optional

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    brand_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("brands.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    city: Mapped[str] = mapped_column(String(200), nullable=False)
    distance: Mapped[Optional[str]] = mapped_column(String(100))

    brand: Mapped["Brand"] = relationship("Brand", back_populates="stores")  # noqa: F821
    product_links: Mapped[List["StoreProduct"]] = relationship("StoreProduct", back_populates="store", lazy="selectin", cascade="all, delete-orphan")


class StoreProduct(Base):
    __tablename__ = "store_products"

    store_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("stores.id"), primary_key=True)
    product_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("products.id"), primary_key=True)

    store: Mapped["Store"] = relationship("Store", back_populates="product_links")
    product: Mapped["Product"] = relationship("Product", back_populates="store_links")  # noqa: F821
