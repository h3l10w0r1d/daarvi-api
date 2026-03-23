from __future__ import annotations
import random
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.outfit import Outfit, OutfitItem, OutfitRating, SavedOutfit
from app.models.product import Product, ProductAvailability, ProductTag


async def get_outfits(db: AsyncSession, scope: str | None = None) -> list[Outfit]:
    stmt = select(Outfit).options(
        selectinload(Outfit.items).selectinload(OutfitItem.product).selectinload(
            Product.brand
        ),
        selectinload(Outfit.items).selectinload(OutfitItem.product).selectinload(
            Product.images
        ),
        selectinload(Outfit.items).selectinload(OutfitItem.product).selectinload(
            Product.colors
        ),
        selectinload(Outfit.items).selectinload(OutfitItem.product).selectinload(
            Product.sizes
        ),
        selectinload(Outfit.items).selectinload(OutfitItem.product).selectinload(
            Product.tags
        ),
        selectinload(Outfit.items).selectinload(OutfitItem.product).selectinload(
            Product.availability
        ),
    )
    if scope and scope != "both":
        stmt = stmt.where(or_(Outfit.scope == scope, Outfit.scope == "both"))
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_outfit(db: AsyncSession, outfit_id: str) -> Outfit | None:
    stmt = (
        select(Outfit)
        .where(Outfit.id == outfit_id)
        .options(
            selectinload(Outfit.items).selectinload(OutfitItem.product).selectinload(
                Product.brand
            ),
            selectinload(Outfit.items).selectinload(OutfitItem.product).selectinload(
                Product.images
            ),
            selectinload(Outfit.items).selectinload(OutfitItem.product).selectinload(
                Product.colors
            ),
            selectinload(Outfit.items).selectinload(OutfitItem.product).selectinload(
                Product.sizes
            ),
            selectinload(Outfit.items).selectinload(OutfitItem.product).selectinload(
                Product.tags
            ),
            selectinload(Outfit.items).selectinload(OutfitItem.product).selectinload(
                Product.availability
            ),
        )
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def generate_outfit(
    db: AsyncSession,
    style: str = "",
    budget: str = "",   # "<300" | "300-800" | "800+"
    occasion: str = "",
    scope: str = "global",
) -> Outfit | None:
    """
    Algorithm:
      1. Build a base product query filtered by scope + price range
      2. Optionally narrow by style keywords → tag matches
      3. Pick one product per role (anchor, top, bottom, accessory)
      4. Return a transient (unsaved) Outfit object
    """
    # ── Price range ──────────────────────────────────────────────────────────
    price_col = Product.price_local if scope == "local" else Product.price_global
    price_filters = []
    if budget == "<300":
        price_filters.append(price_col < 300)
    elif budget == "300-800":
        price_filters.append(and_(price_col >= 300, price_col <= 800))
    elif budget == "800+":
        price_filters.append(price_col > 800)

    # ── Style keyword → tag mapping ──────────────────────────────────────────
    STYLE_TAG_MAP = {
        "dark":        ["dark", "noir", "black", "minimal"],
        "minimalist":  ["minimal", "clean", "simple"],
        "casual":      ["casual", "everyday", "relaxed"],
        "formal":      ["formal", "tailored", "classic"],
        "romantic":    ["romantic", "feminine", "soft"],
        "streetwear":  ["street", "urban", "bold"],
        "sporty":      ["sport", "active", "athletic"],
        "vintage":     ["vintage", "retro", "classic"],
        "luxury":      ["luxury", "premium", "silk"],
        "bohemian":    ["boho", "earthy", "relaxed"],
    }
    style_lower = style.lower()
    tag_keywords: list[str] = []
    for keyword, tags in STYLE_TAG_MAP.items():
        if keyword in style_lower:
            tag_keywords.extend(tags)
    # Also add raw words from the style string
    for word in style_lower.split():
        if len(word) > 3:
            tag_keywords.append(word)

    # ── Role → category mapping ───────────────────────────────────────────────
    ROLE_CATEGORIES: dict[str, list[str]] = {
        "anchor":    ["outerwear", "dresses"],
        "top":       ["tops"],
        "bottom":    ["bottoms"],
        "accessory": ["accessories"],
    }

    async def pick_for_role(role: str, categories: list[str]) -> Product | None:
        base = (
            select(Product)
            .options(
                selectinload(Product.brand),
                selectinload(Product.images),
                selectinload(Product.colors),
                selectinload(Product.sizes),
                selectinload(Product.tags),
                selectinload(Product.availability),
            )
            .where(Product.category.in_(categories))
        )

        # Scope filter
        if scope != "both":
            base = base.join(
                ProductAvailability,
                and_(
                    ProductAvailability.product_id == Product.id,
                    ProductAvailability.mode == scope,
                ),
            )

        if price_filters:
            base = base.where(*price_filters)

        # Try tag-filtered first, fall back to unfiltered
        if tag_keywords:
            tag_stmt = (
                base.join(ProductTag, ProductTag.product_id == Product.id)
                .where(ProductTag.tag.in_(tag_keywords))
                .distinct()
            )
            result = await db.execute(tag_stmt)
            candidates = result.scalars().all()
            if candidates:
                return random.choice(candidates)

        result = await db.execute(base.distinct())
        candidates = result.scalars().all()
        return random.choice(candidates) if candidates else None

    # ── Build outfit items ────────────────────────────────────────────────────
    outfit_items: list[OutfitItem] = []
    anchor_product = None

    for role, cats in ROLE_CATEGORIES.items():
        product = await pick_for_role(role, cats)
        if product is None:
            continue
        item = OutfitItem(
            outfit_id="__generated__",   # transient, not saved
            product_id=product.id,
            role=role,
            is_core=(role in ("anchor", "top", "bottom")),
        )
        item.product = product
        outfit_items.append(item)
        if role == "anchor":
            anchor_product = product

    if not outfit_items:
        return None

    # ── Build transient Outfit ────────────────────────────────────────────────
    import json as _json

    outfit = Outfit(
        id="__generated__",
        title=f"{style.title() or 'Custom'} Outfit",
        description=f"Generated for {occasion or 'any'} occasion.",
        scope=scope,
        occasion=occasion or None,
        style_tags=_json.dumps(tag_keywords[:5]),
        anchor_id=anchor_product.id if anchor_product else None,
    )
    outfit.items = outfit_items
    return outfit


# ─── Saved outfits ────────────────────────────────────────────────────────────

_OUTFIT_LOAD_OPTIONS = [
    selectinload(Outfit.items).selectinload(OutfitItem.product).selectinload(Product.brand),
    selectinload(Outfit.items).selectinload(OutfitItem.product).selectinload(Product.images),
    selectinload(Outfit.items).selectinload(OutfitItem.product).selectinload(Product.colors),
    selectinload(Outfit.items).selectinload(OutfitItem.product).selectinload(Product.sizes),
    selectinload(Outfit.items).selectinload(OutfitItem.product).selectinload(Product.tags),
    selectinload(Outfit.items).selectinload(OutfitItem.product).selectinload(Product.availability),
]


async def save_outfit(db: AsyncSession, user_id: str, outfit_id: str) -> None:
    existing = await db.execute(
        select(SavedOutfit).where(
            and_(SavedOutfit.user_id == user_id, SavedOutfit.outfit_id == outfit_id)
        )
    )
    if not existing.scalars().first():
        db.add(SavedOutfit(user_id=user_id, outfit_id=outfit_id))
        await db.commit()


async def unsave_outfit(db: AsyncSession, user_id: str, outfit_id: str) -> None:
    result = await db.execute(
        select(SavedOutfit).where(
            and_(SavedOutfit.user_id == user_id, SavedOutfit.outfit_id == outfit_id)
        )
    )
    row = result.scalars().first()
    if row:
        await db.delete(row)
        await db.commit()


async def get_saved_outfits(db: AsyncSession, user_id: str) -> list[Outfit]:
    stmt = (
        select(Outfit)
        .join(SavedOutfit, SavedOutfit.outfit_id == Outfit.id)
        .where(SavedOutfit.user_id == user_id)
        .options(*_OUTFIT_LOAD_OPTIONS)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_saved_outfit_ids(db: AsyncSession, user_id: str) -> list[str]:
    result = await db.execute(
        select(SavedOutfit.outfit_id).where(SavedOutfit.user_id == user_id)
    )
    return list(result.scalars().all())


# ─── Outfit ratings ───────────────────────────────────────────────────────────

async def rate_outfit(db: AsyncSession, user_id: str, outfit_id: str, rating: str) -> None:
    result = await db.execute(
        select(OutfitRating).where(
            and_(OutfitRating.user_id == user_id, OutfitRating.outfit_id == outfit_id)
        )
    )
    row = result.scalars().first()
    if row:
        row.rating = rating
    else:
        db.add(OutfitRating(user_id=user_id, outfit_id=outfit_id, rating=rating))
    await db.commit()


# ─── Swap alternatives ────────────────────────────────────────────────────────

_ROLE_CATEGORIES: dict[str, list[str]] = {
    "anchor":    ["outerwear", "dresses"],
    "top":       ["tops"],
    "bottom":    ["bottoms"],
    "shoes":     ["shoes", "footwear"],
    "bag":       ["bags", "accessories"],
    "accessory": ["accessories"],
}

_PRODUCT_LOAD_OPTIONS = [
    selectinload(Product.brand),
    selectinload(Product.images),
    selectinload(Product.colors),
    selectinload(Product.sizes),
    selectinload(Product.tags),
    selectinload(Product.availability),
]


async def get_alternatives(
    db: AsyncSession,
    role: str,
    scope: str,
    exclude_id: str | None = None,
    limit: int = 6,
) -> list[Product]:
    categories = _ROLE_CATEGORIES.get(role, [])
    stmt = select(Product).options(*_PRODUCT_LOAD_OPTIONS)

    if categories:
        stmt = stmt.where(Product.category.in_(categories))
    if exclude_id:
        stmt = stmt.where(Product.id != exclude_id)
    if scope and scope != "both":
        stmt = stmt.join(
            ProductAvailability,
            and_(
                ProductAvailability.product_id == Product.id,
                ProductAvailability.mode == scope,
            ),
        )

    result = await db.execute(stmt.distinct())
    candidates = list(result.scalars().all())
    return random.sample(candidates, min(limit, len(candidates)))
