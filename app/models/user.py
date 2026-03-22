from __future__ import annotations
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(1024), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    dna_profile: Mapped[Optional["DnaProfile"]] = relationship("DnaProfile", back_populates="user", uselist=False, lazy="selectin", cascade="all, delete-orphan")
    wishlist: Mapped[List["Wishlist"]] = relationship("Wishlist", back_populates="user", lazy="selectin", cascade="all, delete-orphan")  # noqa: F821
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="user")  # noqa: F821


class DnaProfile(Base):
    __tablename__ = "dna_profiles"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), unique=True, nullable=False)
    shape: Mapped[Optional[str]] = mapped_column(String(100))
    palette: Mapped[Optional[str]] = mapped_column(String(100))
    budget: Mapped[Optional[str]] = mapped_column(String(100))
    mode: Mapped[Optional[str]] = mapped_column(String(20))

    user: Mapped["User"] = relationship("User", back_populates="dna_profile")
    style_preferences: Mapped[List["DnaStylePreference"]] = relationship("DnaStylePreference", back_populates="dna_profile", lazy="selectin", cascade="all, delete-orphan")


class DnaStylePreference(Base):
    __tablename__ = "dna_style_preferences"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dna_profile_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("dna_profiles.id"), nullable=False)
    style: Mapped[str] = mapped_column(String(100), nullable=False)

    dna_profile: Mapped["DnaProfile"] = relationship("DnaProfile", back_populates="style_preferences")
