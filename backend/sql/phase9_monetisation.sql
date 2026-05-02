CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    subscription_status TEXT DEFAULT 'inactive',
    subscription_plan TEXT DEFAULT 'free',
    free_scans_used INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email
ON users (email);

CREATE TABLE IF NOT EXISTS auth_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    revoked_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_auth_tokens_lookup
ON auth_tokens (token_hash, expires_at, revoked_at);

CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    plan_code TEXT NOT NULL DEFAULT 'free',
    status TEXT NOT NULL DEFAULT 'inactive',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    source TEXT DEFAULT 'internal',
    promo_code TEXT,
    is_auto_renew INTEGER DEFAULT 0,
    monthly_price REAL DEFAULT 5.00,
    currency TEXT DEFAULT 'GBP',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user_status
ON subscriptions (user_id, status, expires_at);

CREATE TABLE IF NOT EXISTS usage_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    barcode TEXT,
    source TEXT DEFAULT 'product_lookup',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_usage_events_user_type
ON usage_events (user_id, event_type, created_at);

ALTER TABLE profiles ADD COLUMN user_id INTEGER;
ALTER TABLE favourites ADD COLUMN user_id INTEGER;
ALTER TABLE scan_history ADD COLUMN user_id INTEGER;

DROP INDEX IF EXISTS idx_favourites_barcode_unique;

CREATE UNIQUE INDEX IF NOT EXISTS idx_favourites_user_barcode_unique
ON favourites (COALESCE(user_id, 0), barcode);
