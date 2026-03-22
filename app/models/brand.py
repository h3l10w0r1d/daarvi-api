from __future__ import annotations
import uuid
from typing import List, Optional

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    tagline: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)
    founded: Mapped[Optional[str]] = mapped_column(String(10))
    origin: Mapped[Optional[str]] = mapped_column(String(200))
    cover_url: Mapped[Optional[str]] = mapped_column(Text)

    products: Mapped[List["Product"]] = relationship("Product", back_populates="brand", lazy="selectin")  # noqa: F821
    stores: Mapped[List["Store"]] = relationship("Store", back_populates="brand", lazy="selectin")  # noqa: F821
