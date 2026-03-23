from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.models import *  # noqa: F401, F403 — registers all models with Base.metadata
from app.database import Base
from app.routers import auth, brands, chat, orders, outfits, products, stores, tryon, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        # Create any brand-new tables
        await conn.run_sync(Base.metadata.create_all)

        # ── Idempotent column / table migrations ──────────────────────────
        # ADD COLUMN IF NOT EXISTS is safe to run on every startup
        await conn.execute(text(
            "ALTER TABLE outfits ADD COLUMN IF NOT EXISTS hero_image TEXT"
        ))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS saved_outfits (
                user_id   UUID NOT NULL REFERENCES users(id)   ON DELETE CASCADE,
                outfit_id UUID NOT NULL REFERENCES outfits(id) ON DELETE CASCADE,
                PRIMARY KEY (user_id, outfit_id)
            )
        """))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS outfit_ratings (
                user_id   UUID        NOT NULL REFERENCES users(id)   ON DELETE CASCADE,
                outfit_id UUID        NOT NULL REFERENCES outfits(id) ON DELETE CASCADE,
                rating    VARCHAR(10) NOT NULL CHECK (rating IN ('up','down')),
                PRIMARY KEY (user_id, outfit_id)
            )
        """))
        # Indexes (IF NOT EXISTS keeps it idempotent)
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_saved_outfits_user_id    ON saved_outfits(user_id)"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_outfit_ratings_user_id   ON outfit_ratings(user_id)"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_outfit_ratings_outfit_id ON outfit_ratings(outfit_id)"
        ))
    yield
    await engine.dispose()


app = FastAPI(
    title="Daarvi API",
    version="1.0.0",
    description="Backend API for the Daarvi fashion platform",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(brands.router)
app.include_router(stores.router)
app.include_router(users.router)
app.include_router(orders.router)
app.include_router(outfits.router)
app.include_router(tryon.router)
app.include_router(chat.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "daarvi-api"}
