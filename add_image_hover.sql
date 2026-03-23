-- ============================================================
-- DAARVI — Add image_hover column to products
-- Run this in TablePlus against your production DB
-- ============================================================

-- 1. Add the column (nullable so existing rows are fine)
ALTER TABLE products ADD COLUMN IF NOT EXISTS image_hover TEXT;

-- 2. Seed some sample hover images for existing products
--    (replace with real product back/detail shots later via admin panel)
UPDATE products SET image_hover = 'https://images.unsplash.com/photo-1594938298603-c8148c4b5d5a?w=800&q=80'
  WHERE id = 'a1000000-0000-0000-0000-000000000001';

UPDATE products SET image_hover = 'https://images.unsplash.com/photo-1506629082955-511b1aa562c8?w=800&q=80'
  WHERE id = 'a1000000-0000-0000-0000-000000000002';

UPDATE products SET image_hover = 'https://images.unsplash.com/photo-1539008835657-9e8e9680c956?w=800&q=80'
  WHERE id = 'a1000000-0000-0000-0000-000000000003';

UPDATE products SET image_hover = 'https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=800&q=80'
  WHERE id = 'a1000000-0000-0000-0000-000000000004';
