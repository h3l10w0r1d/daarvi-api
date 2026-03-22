from __future__ import annotations
import uuid
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.user import DnaProfile, DnaStylePreference, User
from app.models.wishlist import Wishlist

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": user_id, "type": "access", "exp": expire}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode({"sub": user_id, "type": "refresh", "exp": expire}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(
        select(User).where(User.email == email).options(
            selectinload(User.dna_profile).selectinload(DnaProfile.style_preferences),
            selectinload(User.wishlist),
        )
    )
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(
        select(User).where(User.id == user_id).options(
            selectinload(User.dna_profile).selectinload(DnaProfile.style_preferences),
            selectinload(User.wishlist),
        )
    )
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, email: str, name: str, password: str) -> User:
    user = User(id=str(uuid.uuid4()), email=email, name=name, hashed_password=hash_password(password))
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def update_user_name(db: AsyncSession, user: User, name: str) -> User:
    user.name = name
    db.add(user)
    await db.flush()
    return user


async def change_password(db: AsyncSession, user: User, new_password: str) -> None:
    user.hashed_password = hash_password(new_password)
    db.add(user)
    await db.flush()


async def change_email(db: AsyncSession, user: User, new_email: str) -> User:
    user.email = new_email
    db.add(user)
    await db.flush()
    return user


# ─── DNA Profile ──────────────────────────────────────────────────────────────

async def upsert_dna_profile(db: AsyncSession, user: User, data: dict) -> DnaProfile:
    profile = user.dna_profile
    if not profile:
        profile = DnaProfile(id=str(uuid.uuid4()), user_id=user.id)
        db.add(profile)
        await db.flush()

    profile.shape = data.get("shape")
    profile.palette = data.get("palette")
    profile.budget = data.get("budget")
    profile.mode = data.get("mode")

    # Replace style preferences
    await db.execute(delete(DnaStylePreference).where(DnaStylePreference.dna_profile_id == profile.id))
    for style in data.get("style", []):
        db.add(DnaStylePreference(dna_profile_id=profile.id, style=style))

    await db.flush()
    return profile


# ─── Wishlist ─────────────────────────────────────────────────────────────────

async def get_wishlist_product_ids(db: AsyncSession, user_id: str) -> list[str]:
    result = await db.execute(select(Wishlist.product_id).where(Wishlist.user_id == user_id))
    return [row[0] for row in result.fetchall()]


async def add_to_wishlist(db: AsyncSession, user_id: str, product_id: str) -> None:
    existing = await db.execute(
        select(Wishlist).where(Wishlist.user_id == user_id, Wishlist.product_id == product_id)
    )
    if not existing.scalar_one_or_none():
        db.add(Wishlist(user_id=user_id, product_id=product_id))
        await db.flush()


async def remove_from_wishlist(db: AsyncSession, user_id: str, product_id: str) -> None:
    await db.execute(
        delete(Wishlist).where(Wishlist.user_id == user_id, Wishlist.product_id == product_id)
    )
    await db.flush()
