CREATE TABLE IF NOT EXISTS community_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barcode TEXT NOT NULL,
    product_name TEXT NOT NULL,
    feedback_type TEXT NOT NULL,
    comment TEXT NOT NULL,
    allergy_tags_json TEXT DEFAULT '[]',
    condition_tags_json TEXT DEFAULT '[]',
    is_visible INTEGER DEFAULT 1,
    is_flagged INTEGER DEFAULT 0,
    flag_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_community_feedback_barcode_created
ON community_feedback (barcode, created_at DESC, id DESC);

CREATE INDEX IF NOT EXISTS idx_community_feedback_visibility
ON community_feedback (barcode, is_visible, is_flagged);
