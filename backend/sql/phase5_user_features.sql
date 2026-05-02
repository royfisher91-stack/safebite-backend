CREATE TABLE IF NOT EXISTS profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    allergies_json TEXT DEFAULT '[]',
    conditions_json TEXT DEFAULT '[]',
    notes TEXT,
    is_default INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS favourites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barcode TEXT NOT NULL,
    product_name TEXT NOT NULL,
    profile_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_favourites_barcode_unique
ON favourites (barcode);

CREATE TABLE IF NOT EXISTS scan_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barcode TEXT NOT NULL,
    product_name TEXT NOT NULL,
    profile_id INTEGER,
    profile_name TEXT,
    allergies_json TEXT DEFAULT '[]',
    conditions_json TEXT DEFAULT '[]',
    safety_result TEXT,
    safety_score INTEGER,
    condition_results_json TEXT DEFAULT '{}',
    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_scan_history_scanned_at
ON scan_history (scanned_at DESC, id DESC);

CREATE INDEX IF NOT EXISTS idx_favourites_created_at
ON favourites (created_at DESC, id DESC);
