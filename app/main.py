from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.models import *  # noqa: F401, F403 — registers all models with Base.metadata
from app.database import Base
from app.routers import auth, brands, chat, orders, outfits, products, stores, tryon, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (Alembic handles migrations in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
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
