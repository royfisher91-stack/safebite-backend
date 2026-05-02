-- SafeBite Phase 2 schema additions
-- Run this after backing up safebite.db.

CREATE TABLE IF NOT EXISTS product_quality_flags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barcode TEXT NOT NULL,
    flag_name TEXT NOT NULL,
    retailer TEXT,
    source TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS import_validation_issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barcode TEXT,
    product_name TEXT,
    code TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    field_name TEXT,
    retailer TEXT,
    source TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_product_quality_flags_barcode
ON product_quality_flags(barcode);

CREATE INDEX IF NOT EXISTS idx_product_quality_flags_source
ON product_quality_flags(source);

CREATE INDEX IF NOT EXISTS idx_import_validation_issues_barcode
ON import_validation_issues(barcode);

CREATE INDEX IF NOT EXISTS idx_import_validation_issues_source
ON import_validation_issues(source);
