-- ─────────────────────────────────────────────────────────────────────────────
-- Featured page improvements migration
-- Run once in TablePlus against your Render PostgreSQL database
-- ─────────────────────────────────────────────────────────────────────────────

-- 1. Hero image for outfits (editorial lifestyle photo of the full look)
ALTER TABLE outfits
  ADD COLUMN IF NOT EXISTS hero_image TEXT;

-- 2. Saved outfits (user bookmarks)
CREATE TABLE IF NOT EXISTS saved_outfits (
  user_id   UUID NOT NULL REFERENCES users(id)   ON DELETE CASCADE,
  outfit_id UUID NOT NULL REFERENCES outfits(id) ON DELETE CASCADE,
  PRIMARY KEY (user_id, outfit_id)
);

-- 3. Outfit ratings (thumbs up / down per user per outfit)
CREATE TABLE IF NOT EXISTS outfit_ratings (
  user_id   UUID        NOT NULL REFERENCES users(id)   ON DELETE CASCADE,
  outfit_id UUID        NOT NULL REFERENCES outfits(id) ON DELETE CASCADE,
  rating    VARCHAR(10) NOT NULL CHECK (rating IN ('up', 'down')),
  PRIMARY KEY (user_id, outfit_id)
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_saved_outfits_user_id   ON saved_outfits(user_id);
CREATE INDEX IF NOT EXISTS idx_outfit_ratings_user_id  ON outfit_ratings(user_id);
CREATE INDEX IF NOT EXISTS idx_outfit_ratings_outfit_id ON outfit_ratings(outfit_id);
