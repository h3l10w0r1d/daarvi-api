from __future__ import annotations
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Wishlist(Base):
    __tablename__ = "wishlist"

    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), primary_key=True)
    product_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("products.id"), primary_key=True)

    user: Mapped["User"] = relationship("User", back_populates="wishlist")  # noqa: F821
    product: Mapped["Product"] = relationship("Product")  # noqa: F821
