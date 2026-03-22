"""
Seed the database with mock data matching the Daarvi frontend mockData.js.
Run with:  python -m app.seed
"""
import asyncio
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, engine, Base
from app.models import (
    Brand, Product, ProductImage, ProductColor, ProductSize, ProductTag, ProductAvailability,
    Store, StoreProduct,
)

# ─── Brand Data ───────────────────────────────────────────────────────────────

BRANDS = [
    {
        "id": str(uuid.uuid4()), "slug": "maison-noir", "name": "MAISON NOIR",
        "tagline": "Darkness as a design principle.",
        "description": "Born in the 14th arrondissement of Paris, MAISON NOIR is a study in restraint. Every garment begins as a question: what can be removed? The answer is always more than expected. Founder Élise Arnaud trained under three generations of Parisian couturiers before launching the label in 2014 with a single overcoat and a manifesto written on black paper.",
        "founded": "2014", "origin": "Paris, France",
        "cover": "https://images.unsplash.com/photo-1558769132-cb1aea458c5e?w=1400&q=80",
    },
    {
        "id": str(uuid.uuid4()), "slug": "elise-studio", "name": "ÉLISE STUDIO",
        "tagline": "The architecture of the feminine form.",
        "description": "ÉLISE STUDIO was founded on a single belief: that clothing should sculpt space, not just cover skin. Based in a converted Montmartre atelier, each collection is developed through a rigorous process of draping, sketching, and silence. The studio works with a rotating team of artisans, never more than twelve at a time.",
        "founded": "2018", "origin": "Paris, France",
        "cover": "https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=1400&q=80",
    },
    {
        "id": str(uuid.uuid4()), "slug": "corvin", "name": "CORVIN",
        "tagline": "Power dressed quietly.",
        "description": "CORVIN was established in Milan in 2011 by twin designers Marco and Lucia Corvin. Their work explores the tension between masculine tailoring traditions and contemporary fluidity. Every CORVIN jacket is cut from a pattern that has been refined through at least forty iterations.",
        "founded": "2011", "origin": "Milan, Italy",
        "cover": "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=1400&q=80",
    },
    {
        "id": str(uuid.uuid4()), "slug": "nude-form", "name": "NUDE FORM",
        "tagline": "Skin-close. Earth-close.",
        "description": "NUDE FORM was born from a rejection of excess. Founder Soren Lund, a former architect, applies structural thinking to every silhouette. The result: pieces that feel inevitable. Based in Copenhagen, NUDE FORM works exclusively with natural fibers sourced within 500 kilometers of its studio.",
        "founded": "2016", "origin": "Copenhagen, Denmark",
        "cover": "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=1400&q=80",
    },
    {
        "id": str(uuid.uuid4()), "slug": "thread-co", "name": "THREAD & CO",
        "tagline": "Craft as language.",
        "description": "THREAD & CO was founded by knitwear obsessive Hana Mori after a decade spent in Scottish mills and Japanese ateliers learning the language of yarn. Every piece in the collection is hand-finished and takes between three and seven days to produce. The label operates from a small studio in East London.",
        "founded": "2019", "origin": "London, UK",
        "cover": "https://images.unsplash.com/photo-1445205170230-053b83016050?w=1400&q=80",
    },
    {
        "id": str(uuid.uuid4()), "slug": "edge-supply", "name": "EDGE SUPPLY",
        "tagline": "Raw materials. Refined intent.",
        "description": "EDGE SUPPLY started as a leather workshop in Barcelona's El Born neighborhood. Founder Carlos Vega learned his trade from his grandfather, a saddler who made equipment for the Spanish national equestrian team. The brand has expanded into a full ready-to-wear line while maintaining its commitment to hand-finished leather goods.",
        "founded": "2013", "origin": "Barcelona, Spain",
        "cover": "https://images.unsplash.com/photo-1489987707025-afc232f7ea0f?w=1400&q=80",
    },
]

# ─── Product Data ──────────────────────────────────────────────────────────────

def make_products(brands_map: dict) -> list[dict]:
    mn = brands_map["maison-noir"]
    es = brands_map["elise-studio"]
    co = brands_map["corvin"]
    nf = brands_map["nude-form"]
    tc = brands_map["thread-co"]
    ed = brands_map["edge-supply"]

    return [
        {
            "id": str(uuid.uuid4()), "name": "Obsidian Overcoat", "brand_id": mn,
            "category": "outerwear", "price_global": 420, "price_local": 310,
            "delivery_global": "14–21 days", "delivery_local": "3–5 days",
            "material": "80% Wool, 20% Cashmere", "fit": "Oversized",
            "images": [
                "https://images.unsplash.com/photo-1539533018447-63fcce2678e3?w=800&q=80",
                "https://images.unsplash.com/photo-1594938298603-c8148c4b3782?w=800&q=80",
                "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&q=80",
            ],
            "colors": [{"name": "Obsidian", "hex": "#1a1a1a"}, {"name": "Slate", "hex": "#4a4a5a"}],
            "sizes": ["XS", "S", "M", "L", "XL"],
            "tags": ["minimalist", "dark", "structured"],
            "available": ["global", "local"],
        },
        {
            "id": str(uuid.uuid4()), "name": "Ivory Column Dress", "brand_id": es,
            "category": "dresses", "price_global": 280, "price_local": 195,
            "delivery_global": "10–18 days", "delivery_local": "2–4 days",
            "material": "100% Silk Crepe", "fit": "Column",
            "images": [
                "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=800&q=80",
                "https://images.unsplash.com/photo-1566174053879-31528523f8ae?w=800&q=80",
            ],
            "colors": [{"name": "Ivory", "hex": "#fffff0"}, {"name": "Cream", "hex": "#fffdd0"}],
            "sizes": ["XS", "S", "M", "L"],
            "tags": ["minimalist", "classic", "feminine"],
            "available": ["global", "local"],
        },
        {
            "id": str(uuid.uuid4()), "name": "Tailored Wool Blazer", "brand_id": co,
            "category": "tops", "price_global": 560, "price_local": 390,
            "delivery_global": "14–21 days", "delivery_local": "3–5 days",
            "material": "95% Virgin Wool, 5% Elastane", "fit": "Tailored",
            "images": [
                "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=800&q=80",
                "https://images.unsplash.com/photo-1592878904946-b3cd8ae243d0?w=800&q=80",
            ],
            "colors": [{"name": "Charcoal", "hex": "#36454f"}, {"name": "Navy", "hex": "#1f2d5e"}],
            "sizes": ["S", "M", "L", "XL"],
            "tags": ["classic", "structured", "power"],
            "available": ["global"],
        },
        {
            "id": str(uuid.uuid4()), "name": "Sandstone Trousers", "brand_id": nf,
            "category": "bottoms", "price_global": 190, "price_local": 140,
            "delivery_global": "10–18 days", "delivery_local": "2–4 days",
            "material": "100% Organic Cotton", "fit": "Wide Leg",
            "images": [
                "https://images.unsplash.com/photo-1551854838-212c50b4c184?w=800&q=80",
                "https://images.unsplash.com/photo-1506629082955-511b1aa562c8?w=800&q=80",
            ],
            "colors": [{"name": "Sandstone", "hex": "#c2b280"}, {"name": "Clay", "hex": "#b06060"}],
            "sizes": ["XS", "S", "M", "L", "XL"],
            "tags": ["minimalist", "earth", "relaxed"],
            "available": ["local"],
        },
        {
            "id": str(uuid.uuid4()), "name": "Gold Seam Knitwear", "brand_id": tc,
            "category": "tops", "price_global": 230, "price_local": 175,
            "delivery_global": "14–21 days", "delivery_local": "4–7 days",
            "material": "70% Merino Wool, 30% Cashmere", "fit": "Relaxed",
            "images": [
                "https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=800&q=80",
                "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=800&q=80",
            ],
            "colors": [{"name": "Oat", "hex": "#d4c5a9"}, {"name": "Ecru", "hex": "#c2b49a"}],
            "sizes": ["XS", "S", "M", "L"],
            "tags": ["classic", "craft", "warm"],
            "available": ["global"],
        },
        {
            "id": str(uuid.uuid4()), "name": "Carbon Leather Jacket", "brand_id": ed,
            "category": "outerwear", "price_global": 680, "price_local": 520,
            "delivery_global": "14–21 days", "delivery_local": "3–5 days",
            "material": "Full-grain Cowhide Leather", "fit": "Slim",
            "images": [
                "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=800&q=80",
                "https://images.unsplash.com/photo-1520975954732-35dd22299614?w=800&q=80",
            ],
            "colors": [{"name": "Carbon", "hex": "#333333"}, {"name": "Midnight", "hex": "#191970"}],
            "sizes": ["S", "M", "L", "XL", "XXL"],
            "tags": ["dark", "edgy", "structured"],
            "available": ["local"],
        },
        {
            "id": str(uuid.uuid4()), "name": "Linen Shift Dress", "brand_id": es,
            "category": "dresses", "price_global": 210, "price_local": 155,
            "delivery_global": "10–18 days", "delivery_local": "2–4 days",
            "material": "100% Linen", "fit": "Shift",
            "images": [
                "https://images.unsplash.com/photo-1585487000160-6ebcfceb0d03?w=800&q=80",
                "https://images.unsplash.com/photo-1502716119720-b23a93e5fe1b?w=800&q=80",
            ],
            "colors": [{"name": "Stone", "hex": "#928E85"}, {"name": "Sage", "hex": "#8a9a5b"}],
            "sizes": ["XS", "S", "M", "L"],
            "tags": ["minimalist", "relaxed", "feminine"],
            "available": ["global", "local"],
        },
        {
            "id": str(uuid.uuid4()), "name": "Monogram Scarf", "brand_id": mn,
            "category": "accessories", "price_global": 120, "price_local": 90,
            "delivery_global": "7–14 days", "delivery_local": "1–3 days",
            "material": "100% Cashmere", "fit": "One Size",
            "images": [
                "https://images.unsplash.com/photo-1520903920243-00d872a2d1c9?w=800&q=80",
                "https://images.unsplash.com/photo-1520975661595-6453be3f7070?w=800&q=80",
            ],
            "colors": [{"name": "Noir", "hex": "#0d0d0d"}, {"name": "Ivory", "hex": "#fffff0"}],
            "sizes": ["One Size"],
            "tags": ["minimalist", "dark", "classic"],
            "available": ["global", "local"],
        },
    ]


def make_stores(brands_map: dict, products_by_name: dict) -> list[dict]:
    mn = brands_map["maison-noir"]
    es = brands_map["elise-studio"]
    co = brands_map["corvin"]
    nf = brands_map["nude-form"]
    tc = brands_map["thread-co"]
    ed = brands_map["edge-supply"]

    return [
        {
            "id": str(uuid.uuid4()), "name": "MAISON NOIR Flagship", "brand_id": mn,
            "type": "local", "lat": 48.8566, "lng": 2.3522, "city": "Paris", "distance": "1.2 km",
            "product_names": ["Obsidian Overcoat", "Monogram Scarf"],
        },
        {
            "id": str(uuid.uuid4()), "name": "ÉLISE STUDIO", "brand_id": es,
            "type": "local", "lat": 51.5074, "lng": -0.1278, "city": "London", "distance": "3.4 km",
            "product_names": ["Ivory Column Dress", "Linen Shift Dress"],
        },
        {
            "id": str(uuid.uuid4()), "name": "CORVIN House", "brand_id": co,
            "type": "global", "lat": 40.7128, "lng": -74.0060, "city": "New York", "distance": "International",
            "product_names": ["Tailored Wool Blazer"],
        },
        {
            "id": str(uuid.uuid4()), "name": "NUDE FORM Studio", "brand_id": nf,
            "type": "local", "lat": 52.5200, "lng": 13.4050, "city": "Berlin", "distance": "5.7 km",
            "product_names": ["Sandstone Trousers"],
        },
        {
            "id": str(uuid.uuid4()), "name": "THREAD & CO Atelier", "brand_id": tc,
            "type": "global", "lat": 35.6762, "lng": 139.6503, "city": "Tokyo", "distance": "International",
            "product_names": ["Gold Seam Knitwear"],
        },
        {
            "id": str(uuid.uuid4()), "name": "EDGE SUPPLY", "brand_id": ed,
            "type": "local", "lat": 41.3851, "lng": 2.1734, "city": "Barcelona", "distance": "2.1 km",
            "product_names": ["Carbon Leather Jacket"],
        },
    ]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Check if already seeded
        from sqlalchemy import select
        from app.models.brand import Brand as BrandModel
        result = await db.execute(select(BrandModel).limit(1))
        if result.scalar_one_or_none():
            print("✓ Database already seeded, skipping.")
            return

        print("🌱 Seeding brands...")
        brand_orm_map = {}
        brands_slug_to_id = {}
        for b in BRANDS:
            brand = BrandModel(
                id=b["id"], slug=b["slug"], name=b["name"],
                tagline=b["tagline"], description=b["description"],
                founded=b["founded"], origin=b["origin"], cover_url=b["cover"],
            )
            db.add(brand)
            brand_orm_map[b["slug"]] = b["id"]
            brands_slug_to_id[b["slug"]] = b["id"]

        await db.flush()

        print("🌱 Seeding products...")
        products_data = make_products(brand_orm_map)
        product_name_to_id = {}

        for p in products_data:
            product = Product(
                id=p["id"], name=p["name"], brand_id=p["brand_id"],
                category=p["category"], price_global=p["price_global"], price_local=p["price_local"],
                delivery_global=p["delivery_global"], delivery_local=p["delivery_local"],
                material=p["material"], fit=p["fit"],
            )
            db.add(product)
            await db.flush()

            for i, url in enumerate(p["images"]):
                db.add(ProductImage(product_id=p["id"], url=url, position=i))
            for c in p["colors"]:
                db.add(ProductColor(product_id=p["id"], name=c["name"], hex=c["hex"]))
            for s in p["sizes"]:
                db.add(ProductSize(product_id=p["id"], size=s))
            for t in p["tags"]:
                db.add(ProductTag(product_id=p["id"], tag=t))
            for mode in p["available"]:
                db.add(ProductAvailability(product_id=p["id"], mode=mode))

            product_name_to_id[p["name"]] = p["id"]

        await db.flush()

        print("🌱 Seeding stores...")
        from app.models.store import Store as StoreModel, StoreProduct as StoreProductModel
        stores_data = make_stores(brand_orm_map, product_name_to_id)

        for s in stores_data:
            store = StoreModel(
                id=s["id"], name=s["name"], brand_id=s["brand_id"],
                type=s["type"], lat=s["lat"], lng=s["lng"],
                city=s["city"], distance=s["distance"],
            )
            db.add(store)
            await db.flush()

            for pname in s["product_names"]:
                pid = product_name_to_id.get(pname)
                if pid:
                    db.add(StoreProductModel(store_id=s["id"], product_id=pid))

        await db.commit()
        print("✅ Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed())
