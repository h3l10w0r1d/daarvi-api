-- ─────────────────────────────────────────────────────────────────────────────
-- Seed: 2 curated outfits (1 global, 1 local)
-- Run in TablePlus after the backend has started once (tables auto-created).
-- Uses subqueries so it works with any product UUIDs already in the DB.
-- ─────────────────────────────────────────────────────────────────────────────

-- ── Outfit 1: Global — Dark Evening Edit ─────────────────────────────────────
INSERT INTO outfits (id, title, description, scope, occasion, style_tags, anchor_id)
VALUES (
  'of000001-0000-0000-0000-000000000001',
  'Dark Evening Edit',
  'A head-to-toe noir look built around a signature piece. International labels, curated for after dark.',
  'global',
  'evening',
  '["dark","minimalist","noir","luxury"]',
  (SELECT id FROM products WHERE category IN ('outerwear','dresses') ORDER BY price_global DESC LIMIT 1)
)
ON CONFLICT (id) DO NOTHING;

-- Items for Outfit 1
INSERT INTO outfit_items (outfit_id, product_id, role, is_core)
SELECT
  'of000001-0000-0000-0000-000000000001',
  id,
  'anchor',
  true
FROM products
WHERE category IN ('outerwear','dresses')
ORDER BY price_global DESC
LIMIT 1
ON CONFLICT DO NOTHING;

INSERT INTO outfit_items (outfit_id, product_id, role, is_core)
SELECT
  'of000001-0000-0000-0000-000000000001',
  id,
  'top',
  true
FROM products
WHERE category = 'tops'
ORDER BY price_global DESC
LIMIT 1
ON CONFLICT DO NOTHING;

INSERT INTO outfit_items (outfit_id, product_id, role, is_core)
SELECT
  'of000001-0000-0000-0000-000000000001',
  id,
  'bottom',
  true
FROM products
WHERE category = 'bottoms'
ORDER BY price_global DESC
LIMIT 1
ON CONFLICT DO NOTHING;

INSERT INTO outfit_items (outfit_id, product_id, role, is_core)
SELECT
  'of000001-0000-0000-0000-000000000001',
  id,
  'accessory',
  false
FROM products
WHERE category = 'accessories'
ORDER BY price_global DESC
LIMIT 1
ON CONFLICT DO NOTHING;


-- ── Outfit 2: Local — Weekend Casual ─────────────────────────────────────────
INSERT INTO outfits (id, title, description, scope, occasion, style_tags, anchor_id)
VALUES (
  'of000002-0000-0000-0000-000000000002',
  'Weekend Casual',
  'Effortless everyday dressing sourced from nearby boutiques. Same-week delivery, always in season.',
  'local',
  'casual',
  '["casual","minimal","clean","everyday"]',
  (SELECT id FROM products WHERE category IN ('outerwear','tops') ORDER BY price_local ASC LIMIT 1)
)
ON CONFLICT (id) DO NOTHING;

-- Items for Outfit 2
INSERT INTO outfit_items (outfit_id, product_id, role, is_core)
SELECT
  'of000002-0000-0000-0000-000000000002',
  id,
  'anchor',
  true
FROM products
WHERE category IN ('outerwear','tops')
ORDER BY price_local ASC
LIMIT 1
ON CONFLICT DO NOTHING;

INSERT INTO outfit_items (outfit_id, product_id, role, is_core)
SELECT
  'of000002-0000-0000-0000-000000000002',
  id,
  'top',
  true
FROM products
WHERE category = 'tops'
ORDER BY price_local ASC
LIMIT 1 OFFSET 1   -- offset 1 to avoid duplicate of anchor if anchor was a top
ON CONFLICT DO NOTHING;

INSERT INTO outfit_items (outfit_id, product_id, role, is_core)
SELECT
  'of000002-0000-0000-0000-000000000002',
  id,
  'bottom',
  true
FROM products
WHERE category = 'bottoms'
ORDER BY price_local ASC
LIMIT 1
ON CONFLICT DO NOTHING;

INSERT INTO outfit_items (outfit_id, product_id, role, is_core)
SELECT
  'of000002-0000-0000-0000-000000000002',
  id,
  'accessory',
  false
FROM products
WHERE category = 'accessories'
ORDER BY price_local ASC
LIMIT 1
ON CONFLICT DO NOTHING;
