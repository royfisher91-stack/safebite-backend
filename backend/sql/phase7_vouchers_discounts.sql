CREATE TABLE IF NOT EXISTS promo_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    code_type TEXT NOT NULL,
    discount_type TEXT NOT NULL,
    discount_value REAL,
    plan_scope TEXT DEFAULT 'all',
    campaign_label TEXT,
    is_active INTEGER DEFAULT 1,
    usage_limit INTEGER,
    usage_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_promo_codes_active
ON promo_codes (is_active, expires_at, code);

-- Offer promotion fields are added automatically by backend/database.py init_db()
-- so this helper can stay idempotent across SQLite versions that do not support
-- ADD COLUMN IF NOT EXISTS consistently.
