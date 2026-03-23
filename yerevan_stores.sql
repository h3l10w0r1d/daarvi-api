-- ============================================================
-- DAARVI — Yerevan Local Stores
-- Run this in TablePlus against your production DB
-- ============================================================

-- ── NEW BRANDS ───────────────────────────────────────────────
INSERT INTO brands (id, slug, name, tagline, description, founded, origin, cover_url) VALUES
('b2000000-0000-0000-0000-000000000001','ralph-lauren','Ralph Lauren','Redefining American style','Ralph Lauren Corporation is an American luxury fashion house known for its iconic polo shirts, tailored blazers, and timeless Americana aesthetic.','1967','USA','https://images.unsplash.com/photo-1537832816519-689ad163239b?w=1200&q=80'),
('b2000000-0000-0000-0000-000000000002','burberry','Burberry','Britishness and luxury heritage','Burberry is a British luxury fashion house known for its iconic trench coats, distinctive tartan pattern, and heritage-meets-contemporary collections.','1856','United Kingdom','https://images.unsplash.com/photo-1445205170230-053b83016050?w=1200&q=80'),
('b2000000-0000-0000-0000-000000000003','mango','Mango','Fashion from Barcelona','Mango is a Spanish fashion brand known for effortlessly chic Mediterranean style, quality fabrics, and trend-forward designs at accessible prices.','1984','Spain','https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=1200&q=80'),
('b2000000-0000-0000-0000-000000000004','h-and-m','H&M','Fashion and quality at the best price','Hennes & Mauritz is a Swedish multinational clothing retailer offering trendy, affordable fashion for men, women and children globally.','1947','Sweden','https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=1200&q=80'),
('b2000000-0000-0000-0000-000000000005','massimo-dutti','Massimo Dutti','Smart casual and elegant','Massimo Dutti is a Spanish premium clothing brand from the Inditex group, offering refined Mediterranean tailoring and sophisticated casual wear.','1985','Spain','https://images.unsplash.com/photo-1489987707025-afc232f7ea0f?w=1200&q=80'),
('b2000000-0000-0000-0000-000000000006','hugo-boss','Hugo Boss','The new Boss','Hugo Boss is a German luxury fashion house offering premium business, casual and athletic wear for men and women with signature bold design.','1924','Germany','https://images.unsplash.com/photo-1441984904996-e0b6ba687e04?w=1200&q=80'),
('b2000000-0000-0000-0000-000000000007','bershka','Bershka','Streetwear for new generations','Bershka is a Spanish fashion retailer from the Inditex group targeting young shoppers with bold streetwear, urban prints, and trend-led collections.','1998','Spain','https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=1200&q=80')
ON CONFLICT (id) DO NOTHING;

-- ── YEREVAN STORES ───────────────────────────────────────────
-- All stores have type='local' so they appear in LOCAL map mode
-- Coordinates are accurate real-world locations in Yerevan
INSERT INTO stores (id, name, brand_id, type, lat, lng, city, distance) VALUES
-- Dalma Garden Mall cluster (Mashtots Ave 4/6)
('e1000000-0000-0000-0000-000000000001','Zara Yerevan — Dalma','b1000000-0000-0000-0000-000000000001','local',40.18720,44.51440,'Yerevan','3.5 km from centre'),
('e1000000-0000-0000-0000-000000000002','H&M Yerevan — Dalma','b2000000-0000-0000-0000-000000000004','local',40.18700,44.51420,'Yerevan','3.5 km from centre'),
('e1000000-0000-0000-0000-000000000003','Mango Yerevan — Dalma','b2000000-0000-0000-0000-000000000003','local',40.18740,44.51480,'Yerevan','3.5 km from centre'),
('e1000000-0000-0000-0000-000000000004','Massimo Dutti — Dalma','b2000000-0000-0000-0000-000000000005','local',40.18760,44.51500,'Yerevan','3.5 km from centre'),
('e1000000-0000-0000-0000-000000000005','Bershka Yerevan — Dalma','b2000000-0000-0000-0000-000000000007','local',40.18680,44.51380,'Yerevan','3.5 km from centre'),
-- City centre / Northern Avenue
('e1000000-0000-0000-0000-000000000006','Hugo Boss — Northern Ave','b2000000-0000-0000-0000-000000000006','local',40.18430,44.51380,'Yerevan','0.8 km from centre'),
('e1000000-0000-0000-0000-000000000007','Ralph Lauren — Northern Ave','b2000000-0000-0000-0000-000000000001','local',40.18550,44.51050,'Yerevan','1.1 km from centre'),
-- Cascade / Tamanyan area
('e1000000-0000-0000-0000-000000000008','Burberry — Cascade Complex','b2000000-0000-0000-0000-000000000002','local',40.18780,44.50580,'Yerevan','1.8 km from centre')
ON CONFLICT (id) DO NOTHING;
