from __future__ import annotations
import uuid
from typing import List, Optional

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Outfit(Base):
    __tablename__ = "outfits"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    scope: Mapped[str] = mapped_column(String(20), nullable=False)       # "local" | "global" | "both"
    occasion: Mapped[Optional[str]] = mapped_column(String(100))         # "casual" | "evening" | "work" | "weekend"
    style_tags: Mapped[Optional[str]] = mapped_column(Text)              # JSON-encoded list e.g. '["dark","minimalist"]'
    hero_image: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # lifestyle/editorial photo of the full look
    anchor_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )

    items: Mapped[List["OutfitItem"]] = relationship(
        "OutfitItem", lazy="selectin", cascade="all, delete-orphan"
    )


class OutfitItem(Base):
    __tablename__ = "outfit_items"

    outfit_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("outfits.id", ondelete="CASCADE"), primary_key=True
    )
    product_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("products.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)       # "anchor"|"top"|"bottom"|"shoes"|"bag"|"accessory"
    is_core: Mapped[bool] = mapped_column(Boolean, default=True)        # pre-selected by default

    product: Mapped["Product"] = relationship("Product", lazy="selectin")  # noqa: F821


class SavedOutfit(Base):
    """User-saved outfits (bookmarks). Composite PK prevents duplicates."""
    __tablename__ = "saved_outfits"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    outfit_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("outfits.id", ondelete="CASCADE"), primary_key=True
    )


class OutfitRating(Base):
    """Thumbs-up / thumbs-down per user per outfit. Drives personalization."""
    __tablename__ = "outfit_ratings"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    outfit_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("outfits.id", ondelete="CASCADE"), primary_key=True
    )
    rating: Mapped[str] = mapped_column(String(10), nullable=False)     # "up" | "down"
