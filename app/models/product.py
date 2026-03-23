from __future__ import annotations
import uuid
from typing import List, Optional

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    brand_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("brands.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    price_global: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    price_local: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    delivery_global: Mapped[Optional[str]] = mapped_column(String(100))
    delivery_local: Mapped[Optional[str]] = mapped_column(String(100))
    material: Mapped[Optional[str]] = mapped_column(String(300))
    fit: Mapped[Optional[str]] = mapped_column(String(100))
    image_hover: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # secondary/hover image for admin panel + cards

    brand: Mapped["Brand"] = relationship("Brand", back_populates="products")  # noqa: F821
    images: Mapped[List["ProductImage"]] = relationship("ProductImage", back_populates="product", order_by="ProductImage.position", lazy="selectin", cascade="all, delete-orphan")
    colors: Mapped[List["ProductColor"]] = relationship("ProductColor", back_populates="product", lazy="selectin", cascade="all, delete-orphan")
    sizes: Mapped[List["ProductSize"]] = relationship("ProductSize", back_populates="product", lazy="selectin", cascade="all, delete-orphan")
    tags: Mapped[List["ProductTag"]] = relationship("ProductTag", back_populates="product", lazy="selectin", cascade="all, delete-orphan")
    availability: Mapped[List["ProductAvailability"]] = relationship("ProductAvailability", back_populates="product", lazy="selectin", cascade="all, delete-orphan")
    store_links: Mapped[List["StoreProduct"]] = relationship("StoreProduct", back_populates="product")  # noqa: F821


class ProductImage(Base):
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("products.id"), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0)

    product: Mapped["Product"] = relationship("Product", back_populates="images")


class ProductColor(Base):
    __tablename__ = "product_colors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("products.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    hex: Mapped[str] = mapped_column(String(20), nullable=False)

    product: Mapped["Product"] = relationship("Product", back_populates="colors")


class ProductSize(Base):
    __tablename__ = "product_sizes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("products.id"), nullable=False)
    size: Mapped[str] = mapped_column(String(20), nullable=False)

    product: Mapped["Product"] = relationship("Product", back_populates="sizes")


class ProductTag(Base):
    __tablename__ = "product_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("products.id"), nullable=False)
    tag: Mapped[str] = mapped_column(String(100), nullable=False)

    product: Mapped["Product"] = relationship("Product", back_populates="tags")


class ProductAvailability(Base):
    __tablename__ = "product_availability"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("products.id"), nullable=False)
    mode: Mapped[str] = mapped_column(String(20), nullable=False)

    product: Mapped["Product"] = relationship("Product", back_populates="availability")
