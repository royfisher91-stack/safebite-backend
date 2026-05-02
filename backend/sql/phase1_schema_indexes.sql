-- Optional helper indexes for safer/faster Phase 1 work.
-- This file matches the current SafeBite SQLite schema and does not add columns.

CREATE UNIQUE INDEX IF NOT EXISTS idx_products_barcode_unique
ON products(barcode);

CREATE INDEX IF NOT EXISTS idx_products_category_subcategory
ON products(category, subcategory);

CREATE INDEX IF NOT EXISTS idx_offers_barcode
ON offers(barcode);

CREATE INDEX IF NOT EXISTS idx_offers_barcode_retailer
ON offers(barcode, retailer);

CREATE INDEX IF NOT EXISTS idx_offers_price_lookup
ON offers(barcode, stock_status, promo_price, price);
