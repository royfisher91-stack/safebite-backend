import json
import sqlite3
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "safebite.db"
IMPORTS_PRODUCTS_JSON_PATH = BASE_DIR / "imports" / "products.json"
STARTUP_PRODUCT_SEEDS = []

try:
    from data.product_enrichment import PRODUCT_ENRICHMENT
except Exception:
    PRODUCT_ENRICHMENT = {}


def _safe_json_loads(value: Any, default: Any) -> Any:
    if value is None:
        return default

    if isinstance(value, (list, dict)):
        return value

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return default
        try:
            return json.loads(value)
        except Exception:
            return default

    return default


def _safe_json_dumps(value: Any) -> str:
    if value is None:
        return json.dumps([])
    return json.dumps(value, ensure_ascii=False)


def _safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_optional_int(value: Any) -> Optional[int]:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


class DatabaseManager:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = str(db_path or DB_PATH)
        try:
            self.init_db()
        except Exception:
            print("SafeBite database startup: initial import-time init_db failed")
            traceback.print_exc()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT UNIQUE,
                name TEXT,
                brand TEXT,
                description TEXT,
                ingredients TEXT,
                allergens TEXT,
                category TEXT,
                subcategory TEXT,
                image_url TEXT,
                source TEXT,
                source_retailer TEXT,
                safety_score INTEGER,
                safety_result TEXT,
                ingredient_reasoning TEXT,
                allergen_warnings TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS offers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT NOT NULL,
                retailer TEXT,
                price REAL,
                promo_price REAL,
                original_price REAL,
                promo_text TEXT,
                promotion_type TEXT,
                promotion_label TEXT,
                buy_quantity INTEGER,
                pay_quantity INTEGER,
                bundle_price REAL,
                valid_from TIMESTAMP,
                valid_to TIMESTAMP,
                stock_status TEXT,
                in_stock INTEGER DEFAULT 0,
                product_url TEXT,
                image_url TEXT,
                source TEXT,
                source_retailer TEXT,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_offers_unique
            ON offers (barcode, retailer, product_url)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_products_barcode
            ON products (barcode)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_products_name
            ON products (name)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_offers_barcode
            ON offers (barcode)
            """
        )

        cursor.execute(
            """
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
            )
            """
        )

        cursor.execute(
            """
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
            )
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_users_email
            ON users (email)
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                revoked_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_auth_tokens_lookup
            ON auth_tokens (token_hash, expires_at, revoked_at)
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_code TEXT NOT NULL DEFAULT 'free',
                status TEXT NOT NULL DEFAULT 'inactive',
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                cancelled_at TIMESTAMP,
                source TEXT DEFAULT 'internal',
                promo_code TEXT,
                is_auto_renew INTEGER DEFAULT 0,
                monthly_price REAL DEFAULT 5.00,
                currency TEXT DEFAULT 'GBP',
                provider TEXT,
                platform TEXT,
                product_id TEXT,
                purchase_token TEXT,
                transaction_id TEXT,
                add_on_entitlements TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_subscriptions_user_status
            ON subscriptions (user_id, status, expires_at)
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS usage_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                barcode TEXT,
                source TEXT DEFAULT 'product_lookup',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_usage_events_user_type
            ON usage_events (user_id, event_type, created_at)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_promo_codes_active
            ON promo_codes (is_active, expires_at, code)
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                allergies_json TEXT DEFAULT '[]',
                conditions_json TEXT DEFAULT '[]',
                notes TEXT,
                is_default INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS favourites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                barcode TEXT NOT NULL,
                product_name TEXT NOT NULL,
                profile_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self._ensure_column(conn, "favourites", "user_id", "INTEGER")

        cursor.execute(
            """
            DROP INDEX IF EXISTS idx_favourites_barcode_unique
            """
        )

        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_favourites_user_barcode_unique
            ON favourites (COALESCE(user_id, 0), barcode)
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
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
            )
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_scan_history_scanned_at
            ON scan_history (scanned_at DESC, id DESC)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_favourites_created_at
            ON favourites (created_at DESC, id DESC)
            """
        )

        cursor.execute(
            """
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
            )
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_community_feedback_barcode_created
            ON community_feedback (barcode, created_at DESC, id DESC)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_community_feedback_visibility
            ON community_feedback (barcode, is_visible, is_flagged)
            """
        )

        conn.commit()

        self._ensure_column(conn, "products", "description", "TEXT")
        self._ensure_column(conn, "products", "ingredients", "TEXT")
        self._ensure_column(conn, "products", "allergens", "TEXT")
        self._ensure_column(conn, "products", "category", "TEXT")
        self._ensure_column(conn, "products", "subcategory", "TEXT")
        self._ensure_column(conn, "products", "image_url", "TEXT")
        self._ensure_column(conn, "products", "source", "TEXT")
        self._ensure_column(conn, "products", "source_retailer", "TEXT")
        self._ensure_column(conn, "products", "safety_score", "INTEGER")
        self._ensure_column(conn, "products", "safety_result", "TEXT")
        self._ensure_column(conn, "products", "ingredient_reasoning", "TEXT")
        self._ensure_column(conn, "products", "allergen_warnings", "TEXT")
        self._ensure_column(conn, "products", "created_at", "TIMESTAMP")
        self._ensure_column(conn, "products", "updated_at", "TIMESTAMP")

        self._ensure_column(conn, "offers", "promo_price", "REAL")
        self._ensure_column(conn, "offers", "original_price", "REAL")
        self._ensure_column(conn, "offers", "promo_text", "TEXT")
        self._ensure_column(conn, "offers", "promotion_type", "TEXT")
        self._ensure_column(conn, "offers", "promotion_label", "TEXT")
        self._ensure_column(conn, "offers", "buy_quantity", "INTEGER")
        self._ensure_column(conn, "offers", "pay_quantity", "INTEGER")
        self._ensure_column(conn, "offers", "bundle_price", "REAL")
        self._ensure_column(conn, "offers", "valid_from", "TIMESTAMP")
        self._ensure_column(conn, "offers", "valid_to", "TIMESTAMP")
        self._ensure_column(conn, "offers", "stock_status", "TEXT")
        self._ensure_column(conn, "offers", "in_stock", "INTEGER DEFAULT 0")
        self._ensure_column(conn, "offers", "product_url", "TEXT")
        self._ensure_column(conn, "offers", "image_url", "TEXT")
        self._ensure_column(conn, "offers", "source", "TEXT")
        self._ensure_column(conn, "offers", "source_retailer", "TEXT")
        self._ensure_column(conn, "offers", "last_seen", "TIMESTAMP")
        self._ensure_column(conn, "offers", "created_at", "TIMESTAMP")
        self._ensure_column(conn, "offers", "updated_at", "TIMESTAMP")

        self._ensure_column(conn, "promo_codes", "code", "TEXT")
        self._ensure_column(conn, "promo_codes", "code_type", "TEXT")
        self._ensure_column(conn, "promo_codes", "discount_type", "TEXT")
        self._ensure_column(conn, "promo_codes", "discount_value", "REAL")
        self._ensure_column(conn, "promo_codes", "plan_scope", "TEXT DEFAULT 'all'")
        self._ensure_column(conn, "promo_codes", "campaign_label", "TEXT")
        self._ensure_column(conn, "promo_codes", "is_active", "INTEGER DEFAULT 1")
        self._ensure_column(conn, "promo_codes", "usage_limit", "INTEGER")
        self._ensure_column(conn, "promo_codes", "usage_count", "INTEGER DEFAULT 0")
        self._ensure_column(conn, "promo_codes", "expires_at", "TIMESTAMP")
        self._ensure_column(conn, "promo_codes", "notes", "TEXT")
        self._ensure_column(conn, "promo_codes", "created_at", "TIMESTAMP")
        self._ensure_column(conn, "promo_codes", "updated_at", "TIMESTAMP")

        self._ensure_column(conn, "users", "email", "TEXT")
        self._ensure_column(conn, "users", "password_hash", "TEXT")
        self._ensure_column(conn, "users", "is_active", "INTEGER DEFAULT 1")
        self._ensure_column(conn, "users", "subscription_status", "TEXT DEFAULT 'inactive'")
        self._ensure_column(conn, "users", "subscription_plan", "TEXT DEFAULT 'free'")
        self._ensure_column(conn, "users", "free_scans_used", "INTEGER DEFAULT 0")
        self._ensure_column(conn, "users", "created_at", "TIMESTAMP")
        self._ensure_column(conn, "users", "updated_at", "TIMESTAMP")

        self._ensure_column(conn, "auth_tokens", "user_id", "INTEGER")
        self._ensure_column(conn, "auth_tokens", "token_hash", "TEXT")
        self._ensure_column(conn, "auth_tokens", "created_at", "TIMESTAMP")
        self._ensure_column(conn, "auth_tokens", "expires_at", "TIMESTAMP")
        self._ensure_column(conn, "auth_tokens", "revoked_at", "TIMESTAMP")

        self._ensure_column(conn, "subscriptions", "user_id", "INTEGER")
        self._ensure_column(conn, "subscriptions", "plan_code", "TEXT DEFAULT 'free'")
        self._ensure_column(conn, "subscriptions", "status", "TEXT DEFAULT 'inactive'")
        self._ensure_column(conn, "subscriptions", "started_at", "TIMESTAMP")
        self._ensure_column(conn, "subscriptions", "expires_at", "TIMESTAMP")
        self._ensure_column(conn, "subscriptions", "cancelled_at", "TIMESTAMP")
        self._ensure_column(conn, "subscriptions", "source", "TEXT DEFAULT 'internal'")
        self._ensure_column(conn, "subscriptions", "promo_code", "TEXT")
        self._ensure_column(conn, "subscriptions", "is_auto_renew", "INTEGER DEFAULT 0")
        self._ensure_column(conn, "subscriptions", "monthly_price", "REAL DEFAULT 5.00")
        self._ensure_column(conn, "subscriptions", "currency", "TEXT DEFAULT 'GBP'")
        self._ensure_column(conn, "subscriptions", "provider", "TEXT")
        self._ensure_column(conn, "subscriptions", "platform", "TEXT")
        self._ensure_column(conn, "subscriptions", "product_id", "TEXT")
        self._ensure_column(conn, "subscriptions", "purchase_token", "TEXT")
        self._ensure_column(conn, "subscriptions", "transaction_id", "TEXT")
        self._ensure_column(conn, "subscriptions", "add_on_entitlements", "TEXT DEFAULT '[]'")
        self._ensure_column(conn, "subscriptions", "created_at", "TIMESTAMP")
        self._ensure_column(conn, "subscriptions", "updated_at", "TIMESTAMP")

        self._ensure_column(conn, "usage_events", "user_id", "INTEGER")
        self._ensure_column(conn, "usage_events", "event_type", "TEXT")
        self._ensure_column(conn, "usage_events", "barcode", "TEXT")
        self._ensure_column(conn, "usage_events", "source", "TEXT DEFAULT 'product_lookup'")
        self._ensure_column(conn, "usage_events", "created_at", "TIMESTAMP")

        cursor.execute(
            """
            UPDATE users
            SET is_active = 1
            WHERE is_active IS NULL
            """
        )
        cursor.execute(
            """
            UPDATE users
            SET subscription_status = 'inactive'
            WHERE subscription_status IS NULL OR TRIM(subscription_status) = ''
            """
        )
        cursor.execute(
            """
            UPDATE users
            SET subscription_plan = 'free'
            WHERE subscription_plan IS NULL OR TRIM(subscription_plan) = ''
            """
        )
        cursor.execute(
            """
            UPDATE users
            SET free_scans_used = 0
            WHERE free_scans_used IS NULL
            """
        )
        cursor.execute(
            """
            UPDATE users
            SET created_at = CURRENT_TIMESTAMP
            WHERE created_at IS NULL
            """
        )
        cursor.execute(
            """
            UPDATE users
            SET updated_at = CURRENT_TIMESTAMP
            WHERE updated_at IS NULL
            """
        )

        self._ensure_column(conn, "profiles", "user_id", "INTEGER")
        self._ensure_column(conn, "profiles", "name", "TEXT")
        self._ensure_column(conn, "profiles", "allergies_json", "TEXT DEFAULT '[]'")
        self._ensure_column(conn, "profiles", "conditions_json", "TEXT DEFAULT '[]'")
        self._ensure_column(conn, "profiles", "notes", "TEXT")
        self._ensure_column(conn, "profiles", "is_default", "INTEGER DEFAULT 0")
        self._ensure_column(conn, "profiles", "created_at", "TIMESTAMP")
        self._ensure_column(conn, "profiles", "updated_at", "TIMESTAMP")

        self._ensure_column(conn, "favourites", "user_id", "INTEGER")
        self._ensure_column(conn, "favourites", "barcode", "TEXT")
        self._ensure_column(conn, "favourites", "product_name", "TEXT")
        self._ensure_column(conn, "favourites", "profile_id", "INTEGER")
        self._ensure_column(conn, "favourites", "created_at", "TIMESTAMP")

        self._ensure_column(conn, "scan_history", "user_id", "INTEGER")
        self._ensure_column(conn, "scan_history", "barcode", "TEXT")
        self._ensure_column(conn, "scan_history", "product_name", "TEXT")
        self._ensure_column(conn, "scan_history", "profile_id", "INTEGER")
        self._ensure_column(conn, "scan_history", "profile_name", "TEXT")
        self._ensure_column(conn, "scan_history", "allergies_json", "TEXT DEFAULT '[]'")
        self._ensure_column(conn, "scan_history", "conditions_json", "TEXT DEFAULT '[]'")
        self._ensure_column(conn, "scan_history", "safety_result", "TEXT")
        self._ensure_column(conn, "scan_history", "safety_score", "INTEGER")
        self._ensure_column(conn, "scan_history", "condition_results_json", "TEXT DEFAULT '{}'")
        self._ensure_column(conn, "scan_history", "scanned_at", "TIMESTAMP")

        self._ensure_column(conn, "community_feedback", "barcode", "TEXT")
        self._ensure_column(conn, "community_feedback", "product_name", "TEXT")
        self._ensure_column(conn, "community_feedback", "feedback_type", "TEXT")
        self._ensure_column(conn, "community_feedback", "comment", "TEXT")
        self._ensure_column(conn, "community_feedback", "allergy_tags_json", "TEXT DEFAULT '[]'")
        self._ensure_column(conn, "community_feedback", "condition_tags_json", "TEXT DEFAULT '[]'")
        self._ensure_column(conn, "community_feedback", "is_visible", "INTEGER DEFAULT 1")
        self._ensure_column(conn, "community_feedback", "is_flagged", "INTEGER DEFAULT 0")
        self._ensure_column(conn, "community_feedback", "flag_reason", "TEXT")
        self._ensure_column(conn, "community_feedback", "created_at", "TIMESTAMP")
        self._ensure_column(conn, "community_feedback", "updated_at", "TIMESTAMP")

        cursor.execute(
            """
            UPDATE products
            SET created_at = CURRENT_TIMESTAMP
            WHERE created_at IS NULL
            """
        )
        cursor.execute(
            """
            UPDATE products
            SET updated_at = CURRENT_TIMESTAMP
            WHERE updated_at IS NULL
            """
        )
        cursor.execute(
            """
            UPDATE offers
            SET last_seen = CURRENT_TIMESTAMP
            WHERE last_seen IS NULL
            """
        )
        cursor.execute(
            """
            UPDATE offers
            SET created_at = CURRENT_TIMESTAMP
            WHERE created_at IS NULL
            """
        )
        cursor.execute(
            """
            UPDATE offers
            SET updated_at = CURRENT_TIMESTAMP
            WHERE updated_at IS NULL
            """
        )
        cursor.execute(
            """
            UPDATE promo_codes
            SET plan_scope = 'all'
            WHERE plan_scope IS NULL OR TRIM(plan_scope) = ''
            """
        )
        cursor.execute(
            """
            UPDATE promo_codes
            SET is_active = 1
            WHERE is_active IS NULL
            """
        )
        cursor.execute(
            """
            UPDATE promo_codes
            SET usage_count = 0
            WHERE usage_count IS NULL
            """
        )
        cursor.execute(
            """
            UPDATE promo_codes
            SET created_at = CURRENT_TIMESTAMP
            WHERE created_at IS NULL
            """
        )
        cursor.execute(
            """
            UPDATE promo_codes
            SET updated_at = CURRENT_TIMESTAMP
            WHERE updated_at IS NULL
            """
        )
        cursor.execute(
            """
            UPDATE profiles
            SET allergies_json = '[]'
            WHERE allergies_json IS NULL OR TRIM(allergies_json) = ''
            """
        )
        cursor.execute(
            """
            UPDATE profiles
            SET conditions_json = '[]'
            WHERE conditions_json IS NULL OR TRIM(conditions_json) = ''
            """
        )
        cursor.execute(
            """
            UPDATE profiles
            SET created_at = CURRENT_TIMESTAMP
            WHERE created_at IS NULL
            """
        )
        cursor.execute(
            """
            UPDATE profiles
            SET updated_at = CURRENT_TIMESTAMP
            WHERE updated_at IS NULL
            """
        )
        cursor.execute(
            """
            UPDATE favourites
            SET created_at = CURRENT_TIMESTAMP
            WHERE created_at IS NULL
            """
        )
        cursor.execute(
            """
            UPDATE scan_history
            SET allergies_json = '[]'
            WHERE allergies_json IS NULL OR TRIM(allergies_json) = ''
            """
        )
        cursor.execute(
            """
            UPDATE scan_history
            SET conditions_json = '[]'
            WHERE conditions_json IS NULL OR TRIM(conditions_json) = ''
            """
        )
        cursor.execute(
            """
            UPDATE scan_history
            SET condition_results_json = '{}'
            WHERE condition_results_json IS NULL OR TRIM(condition_results_json) = ''
            """
        )
        cursor.execute(
            """
            UPDATE scan_history
            SET scanned_at = CURRENT_TIMESTAMP
            WHERE scanned_at IS NULL
            """
        )
        cursor.execute(
            """
            UPDATE community_feedback
            SET allergy_tags_json = '[]'
            WHERE allergy_tags_json IS NULL OR TRIM(allergy_tags_json) = ''
            """
        )
        cursor.execute(
            """
            UPDATE community_feedback
            SET condition_tags_json = '[]'
            WHERE condition_tags_json IS NULL OR TRIM(condition_tags_json) = ''
            """
        )
        cursor.execute(
            """
            UPDATE community_feedback
            SET is_visible = 1
            WHERE is_visible IS NULL
            """
        )
        cursor.execute(
            """
            UPDATE community_feedback
            SET is_flagged = 0
            WHERE is_flagged IS NULL
            """
        )
        cursor.execute(
            """
            UPDATE community_feedback
            SET created_at = CURRENT_TIMESTAMP
            WHERE created_at IS NULL
            """
        )
        cursor.execute(
            """
            UPDATE community_feedback
            SET updated_at = CURRENT_TIMESTAMP
            WHERE updated_at IS NULL
            """
        )

        conn.commit()
        conn.close()

    def _ensure_column(
        self,
        conn: sqlite3.Connection,
        table_name: str,
        column_name: str,
        column_type: str,
    ) -> None:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info({})".format(table_name))
        columns = [row["name"] for row in cursor.fetchall()]

        if column_name not in columns:
            cursor.execute(
                "ALTER TABLE {} ADD COLUMN {} {}".format(
                    table_name,
                    column_name,
                    column_type,
                )
            )

    def _apply_product_enrichment(self, product: Dict[str, Any]) -> Dict[str, Any]:
        barcode = str(product.get("barcode") or "").strip()
        if not barcode:
            return product

        enrichment = PRODUCT_ENRICHMENT.get(barcode)
        if not enrichment:
            return product

        if _is_blank(product.get("name")) or product.get("name") == "Unknown product":
            if not _is_blank(enrichment.get("name")):
                product["name"] = enrichment.get("name")

        if _is_blank(product.get("brand")):
            if not _is_blank(enrichment.get("brand")):
                product["brand"] = enrichment.get("brand")

        if _is_blank(product.get("description")):
            if not _is_blank(enrichment.get("description")):
                product["description"] = enrichment.get("description")

        if _is_blank(product.get("category")):
            if not _is_blank(enrichment.get("category")):
                product["category"] = enrichment.get("category")

        if _is_blank(product.get("subcategory")):
            if not _is_blank(enrichment.get("subcategory")):
                product["subcategory"] = enrichment.get("subcategory")

        if _is_blank(product.get("source")):
            if not _is_blank(enrichment.get("source")):
                product["source"] = enrichment.get("source")

        if _is_blank(product.get("source_retailer")):
            if not _is_blank(enrichment.get("source_retailer")):
                product["source_retailer"] = enrichment.get("source_retailer")

        current_ingredients = product.get("ingredients") or []
        current_allergens = product.get("allergens") or []

        if not current_ingredients:
            product["ingredients"] = enrichment.get("ingredients", [])

        if not current_allergens:
            product["allergens"] = enrichment.get("allergens", [])

        return product

    def _normalize_stock_status(
        self,
        stock_status: Optional[str],
        in_stock: bool,
    ) -> str:
        if stock_status and str(stock_status).strip():
            return str(stock_status).strip()

        return "in_stock" if in_stock else "unknown"

    def _row_to_product_dict(self, row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
        if row is None:
            return None

        product = dict(row)
        product["ingredients"] = _safe_json_loads(product.get("ingredients"), [])
        product["allergens"] = _safe_json_loads(product.get("allergens"), [])
        product["safety_score"] = _safe_optional_int(product.get("safety_score"))
        product["safety_result"] = product.get("safety_result") or ("Unknown" if product["safety_score"] is None else "Caution")
        product["ingredient_reasoning"] = product.get("ingredient_reasoning") or ""
        product["allergen_warnings"] = product.get("allergen_warnings") or ""
        product["description"] = product.get("description") or ""
        product["source"] = product.get("source")
        product["source_retailer"] = product.get("source_retailer")

        return self._apply_product_enrichment(product)

    def _row_to_offer_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        raw = dict(row)

        in_stock = bool(raw.get("in_stock"))
        product_url = raw.get("product_url") or raw.get("url") or ""

        offer = {
            "id": raw.get("id"),
            "barcode": raw.get("barcode"),
            "retailer": raw.get("retailer"),
            "price": _safe_float(raw.get("price")),
            "promo_price": _safe_float(raw.get("promo_price")),
            "original_price": _safe_float(raw.get("original_price")),
            "promo_text": raw.get("promo_text") or "",
            "promotion_type": raw.get("promotion_type") or "",
            "promotion_label": raw.get("promotion_label") or "",
            "buy_quantity": _safe_optional_int(raw.get("buy_quantity")),
            "pay_quantity": _safe_optional_int(raw.get("pay_quantity")),
            "bundle_price": _safe_float(raw.get("bundle_price")),
            "valid_from": raw.get("valid_from"),
            "valid_to": raw.get("valid_to"),
            "stock_status": self._normalize_stock_status(raw.get("stock_status"), in_stock),
            "in_stock": in_stock,
            "product_url": product_url,
            "image_url": raw.get("image_url") or "",
            "source": raw.get("source") or "",
            "source_retailer": raw.get("source_retailer") or "",
            "last_seen": raw.get("last_seen"),
            "created_at": raw.get("created_at"),
            "updated_at": raw.get("updated_at"),
        }

        return offer

    def upsert_product(self, product_data: Dict[str, Any]) -> None:
        barcode = str(product_data.get("barcode") or "").strip()
        if not barcode:
            return

        name = product_data.get("name")
        brand = product_data.get("brand")
        description = product_data.get("description")
        ingredients = product_data.get("ingredients") or []
        allergens = product_data.get("allergens") or []
        category = product_data.get("category")
        subcategory = product_data.get("subcategory")
        image_url = product_data.get("image_url")
        source = product_data.get("source")
        source_retailer = product_data.get("source_retailer")
        safety_score = product_data.get("safety_score")
        safety_result = product_data.get("safety_result")
        ingredient_reasoning = product_data.get("ingredient_reasoning")
        allergen_warnings = product_data.get("allergen_warnings")

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM products
            WHERE barcode = ?
            """,
            (barcode,),
        )
        existing = cursor.fetchone()

        if existing:
            existing_dict = dict(existing)

            final_name = name if name not in (None, "", "Unknown product") else existing_dict.get("name")
            final_brand = brand if not _is_blank(brand) else existing_dict.get("brand")
            final_description = description if not _is_blank(description) else existing_dict.get("description")
            final_category = category if not _is_blank(category) else existing_dict.get("category")
            final_subcategory = subcategory if not _is_blank(subcategory) else existing_dict.get("subcategory")
            final_image_url = image_url if not _is_blank(image_url) else existing_dict.get("image_url")
            final_source = source if not _is_blank(source) else existing_dict.get("source")
            final_source_retailer = (
                source_retailer if not _is_blank(source_retailer) else existing_dict.get("source_retailer")
            )

            existing_ingredients = _safe_json_loads(existing_dict.get("ingredients"), [])
            existing_allergens = _safe_json_loads(existing_dict.get("allergens"), [])

            final_ingredients = ingredients if ingredients else existing_ingredients
            final_allergens = allergens if allergens else existing_allergens

            final_safety_score = (
                safety_score if safety_score not in (None, "") else existing_dict.get("safety_score")
            )
            final_safety_result = (
                safety_result if safety_result not in (None, "") else existing_dict.get("safety_result")
            )
            final_ingredient_reasoning = (
                ingredient_reasoning
                if ingredient_reasoning not in (None, "")
                else existing_dict.get("ingredient_reasoning")
            )
            final_allergen_warnings = (
                allergen_warnings
                if allergen_warnings not in (None, "")
                else existing_dict.get("allergen_warnings")
            )

            cursor.execute(
                """
                UPDATE products
                SET
                    name = ?,
                    brand = ?,
                    description = ?,
                    ingredients = ?,
                    allergens = ?,
                    category = ?,
                    subcategory = ?,
                    image_url = ?,
                    source = ?,
                    source_retailer = ?,
                    safety_score = ?,
                    safety_result = ?,
                    ingredient_reasoning = ?,
                    allergen_warnings = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE barcode = ?
                """,
                (
                    final_name,
                    final_brand,
                    final_description,
                    _safe_json_dumps(final_ingredients),
                    _safe_json_dumps(final_allergens),
                    final_category,
                    final_subcategory,
                    final_image_url,
                    final_source,
                    final_source_retailer,
                    final_safety_score,
                    final_safety_result,
                    final_ingredient_reasoning,
                    final_allergen_warnings,
                    barcode,
                ),
            )
        else:
            cursor.execute(
                """
                INSERT INTO products (
                    barcode,
                    name,
                    brand,
                    description,
                    ingredients,
                    allergens,
                    category,
                    subcategory,
                    image_url,
                    source,
                    source_retailer,
                    safety_score,
                    safety_result,
                    ingredient_reasoning,
                    allergen_warnings
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    barcode,
                    name,
                    brand,
                    description,
                    _safe_json_dumps(ingredients),
                    _safe_json_dumps(allergens),
                    category,
                    subcategory,
                    image_url,
                    source,
                    source_retailer,
                    safety_score,
                    safety_result,
                    ingredient_reasoning,
                    allergen_warnings,
                ),
            )

        conn.commit()
        conn.close()

    def upsert_offer(self, offer_data: Dict[str, Any]) -> None:
        barcode = str(offer_data.get("barcode") or "").strip()
        retailer = (offer_data.get("retailer") or "").strip()
        product_url = (offer_data.get("product_url") or "").strip()

        if not barcode or not retailer:
            return

        price = _safe_float(offer_data.get("price"))
        promo_price = _safe_float(offer_data.get("promo_price"))
        original_price = _safe_float(offer_data.get("original_price"))
        promo_text = offer_data.get("promo_text")
        promotion_type = offer_data.get("promotion_type")
        promotion_label = offer_data.get("promotion_label")
        buy_quantity = _safe_optional_int(offer_data.get("buy_quantity"))
        pay_quantity = _safe_optional_int(offer_data.get("pay_quantity"))
        bundle_price = _safe_float(offer_data.get("bundle_price"))
        valid_from = offer_data.get("valid_from")
        valid_to = offer_data.get("valid_to")
        stock_status = offer_data.get("stock_status")
        image_url = offer_data.get("image_url")
        source = offer_data.get("source")
        source_retailer = offer_data.get("source_retailer")
        in_stock = 1 if offer_data.get("in_stock") else 0

        conn = self.get_connection()
        cursor = conn.cursor()

        existing = None

        if product_url:
            cursor.execute(
                """
                SELECT id
                FROM offers
                WHERE barcode = ? AND retailer = ? AND product_url = ?
                LIMIT 1
                """,
                (barcode, retailer, product_url),
            )
            existing = cursor.fetchone()

        if not existing:
            cursor.execute(
                """
                SELECT id
                FROM offers
                WHERE barcode = ? AND retailer = ?
                LIMIT 1
                """,
                (barcode, retailer),
            )
            existing = cursor.fetchone()

        if existing:
            cursor.execute(
                """
                UPDATE offers
                SET
                    price = ?,
                    promo_price = ?,
                    original_price = ?,
                    promo_text = ?,
                    promotion_type = ?,
                    promotion_label = ?,
                    buy_quantity = ?,
                    pay_quantity = ?,
                    bundle_price = ?,
                    valid_from = ?,
                    valid_to = ?,
                    stock_status = ?,
                    in_stock = ?,
                    product_url = ?,
                    image_url = ?,
                    source = ?,
                    source_retailer = ?,
                    last_seen = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    price,
                    promo_price,
                    original_price,
                    promo_text,
                    promotion_type,
                    promotion_label,
                    buy_quantity,
                    pay_quantity,
                    bundle_price,
                    valid_from,
                    valid_to,
                    stock_status,
                    in_stock,
                    product_url,
                    image_url,
                    source,
                    source_retailer,
                    existing["id"],
                ),
            )
        else:
            cursor.execute(
                """
                INSERT INTO offers (
                    barcode,
                    retailer,
                    price,
                    promo_price,
                    original_price,
                    promo_text,
                    promotion_type,
                    promotion_label,
                    buy_quantity,
                    pay_quantity,
                    bundle_price,
                    valid_from,
                    valid_to,
                    stock_status,
                    in_stock,
                    product_url,
                    image_url,
                    source,
                    source_retailer
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    barcode,
                    retailer,
                    price,
                    promo_price,
                    original_price,
                    promo_text,
                    promotion_type,
                    promotion_label,
                    buy_quantity,
                    pay_quantity,
                    bundle_price,
                    valid_from,
                    valid_to,
                    stock_status,
                    in_stock,
                    product_url,
                    image_url,
                    source,
                    source_retailer,
                ),
            )

        conn.commit()
        conn.close()

    def get_product_by_barcode(self, barcode: str) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM products
            WHERE barcode = ?
            LIMIT 1
            """,
            (barcode,),
        )
        row = cursor.fetchone()
        conn.close()

        return self._row_to_product_dict(row)

    def get_product_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM products
            WHERE LOWER(name) = LOWER(?)
            LIMIT 1
            """,
            (name,),
        )
        row = cursor.fetchone()
        conn.close()

        return self._row_to_product_dict(row)

    def search_products(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        search = "%{}%".format(query.strip())
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM products
            WHERE
                name LIKE ?
                OR brand LIKE ?
                OR barcode LIKE ?
                OR category LIKE ?
                OR subcategory LIKE ?
            ORDER BY name ASC
            LIMIT ?
            """,
            (search, search, search, search, search, limit),
        )

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_product_dict(row) for row in rows if row is not None]

    def list_products(self, limit: int = 100) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM products
            ORDER BY updated_at DESC, name ASC
            LIMIT ?
            """,
            (limit,),
        )

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_product_dict(row) for row in rows if row is not None]

    def get_all_products(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self.list_products(limit=limit)

    def get_offers_by_barcode(self, barcode: str) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM offers
            WHERE barcode = ?
            ORDER BY
                CASE
                    WHEN promo_price IS NOT NULL AND promo_price > 0 THEN promo_price
                    WHEN price IS NOT NULL THEN price
                    ELSE 999999
                END ASC,
                retailer ASC
            """,
            (barcode,),
        )

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_offer_dict(row) for row in rows]

    def get_products_by_category(
        self,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        exclude_barcode: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()

        conditions = []
        params = []

        if category:
            conditions.append("category = ?")
            params.append(category)

        if subcategory:
            conditions.append("subcategory = ?")
            params.append(subcategory)

        if exclude_barcode:
            conditions.append("barcode != ?")
            params.append(exclude_barcode)

        where_sql = ""
        if conditions:
            where_sql = "WHERE " + " AND ".join(conditions)

        sql = """
            SELECT *
            FROM products
            {}
            ORDER BY name ASC
            LIMIT ?
        """.format(where_sql)

        params.append(limit)

        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_product_dict(row) for row in rows if row is not None]

    def get_similar_products(
        self,
        product: Dict[str, Any],
        limit: int = 6,
    ) -> List[Dict[str, Any]]:
        barcode = product.get("barcode")
        subcategory = product.get("subcategory")
        category = product.get("category")

        if subcategory:
            same_subcategory = self.get_products_by_category(
                category=category,
                subcategory=subcategory,
                exclude_barcode=barcode,
                limit=limit,
            )
            if same_subcategory:
                return same_subcategory[:limit]

        if category:
            same_category = self.get_products_by_category(
                category=category,
                subcategory=None,
                exclude_barcode=barcode,
                limit=limit,
            )
            if same_category:
                return same_category[:limit]

        return []

    def get_product_count(self) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS count FROM products")
        row = cursor.fetchone()
        conn.close()
        return int(row["count"]) if row else 0

    def get_offer_count(self) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS count FROM offers")
        row = cursor.fetchone()
        conn.close()
        return int(row["count"]) if row else 0

    def seed_products_from_json(self, path: Optional[Path] = None) -> int:
        file_path = Path(path) if path else IMPORTS_PRODUCTS_JSON_PATH

        if not file_path.exists():
            print(f"SafeBite startup: products seed file not found: {file_path}")
            return 0

        try:
            raw = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            print(f"SafeBite startup: failed to read products seed file: {file_path}")
            traceback.print_exc()
            return 0

        items = []
        if isinstance(raw, list):
            items = raw
        elif isinstance(raw, dict):
            if isinstance(raw.get("products"), list):
                items = raw.get("products", [])
            elif isinstance(raw.get("items"), list):
                items = raw.get("items", [])

        seeded = 0

        for item in items:
            if not isinstance(item, dict):
                continue

            barcode = str(item.get("barcode") or "").strip()
            if not barcode:
                continue

            product_payload = {
                "barcode": barcode,
                "name": item.get("name") or item.get("title") or "Unknown product",
                "brand": item.get("brand") or "",
                "description": item.get("description") or "",
                "ingredients": item.get("ingredients") or [],
                "allergens": item.get("allergens") or [],
                "category": item.get("category") or "",
                "subcategory": item.get("subcategory") or "",
                "image_url": item.get("image_url") or item.get("image") or "",
                "source": item.get("source") or "products_json_seed",
                "source_retailer": item.get("source_retailer") or "SafeBite",
                "safety_score": item.get("safety_score"),
                "safety_result": item.get("safety_result"),
                "ingredient_reasoning": item.get("ingredient_reasoning"),
                "allergen_warnings": item.get("allergen_warnings"),
            }

            self.upsert_product(product_payload)
            seeded += 1

        return seeded

    def seed_startup_products(self) -> int:
        seeded = 0

        for item in STARTUP_PRODUCT_SEEDS:
            barcode = str(item.get("barcode") or "").strip()
            if not barcode:
                continue

            if self.get_product_by_barcode(barcode):
                continue

            self.upsert_product(item)
            seeded += 1

        return seeded

    def seed_sample_offers(self) -> int:
        sample_offers = []

        seeded = 0

        for offer in sample_offers:
            product = self.get_product_by_barcode(offer["barcode"])
            if not product:
                continue

            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id
                FROM offers
                WHERE barcode = ?
                  AND retailer = ?
                LIMIT 1
                """,
                (offer["barcode"], offer["retailer"]),
            )
            existing_offer = cursor.fetchone()

            if existing_offer:
                cursor.execute(
                    """
                    UPDATE offers
                    SET source = ?,
                        source_retailer = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                      AND LOWER(TRIM(source)) = 'sample_seed'
                    """,
                    (
                        offer["source"],
                        offer["source_retailer"],
                        existing_offer["id"],
                    ),
                )
                conn.commit()
                conn.close()
                continue

            conn.close()

            self.upsert_offer(offer)
            seeded += 1

        return seeded


db = DatabaseManager()


def init_db() -> None:
    db.init_db()


def upsert_product(product_data: Dict[str, Any]) -> None:
    db.upsert_product(product_data)


def upsert_offer(offer_data: Dict[str, Any]) -> None:
    db.upsert_offer(offer_data)


def get_product_by_barcode(barcode: str) -> Optional[Dict[str, Any]]:
    return db.get_product_by_barcode(barcode)


def get_product_by_name(name: str) -> Optional[Dict[str, Any]]:
    return db.get_product_by_name(name)


def search_products(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    return db.search_products(query=query, limit=limit)


def list_products(limit: int = 100) -> List[Dict[str, Any]]:
    return db.list_products(limit=limit)


def get_all_products(limit: int = 100) -> List[Dict[str, Any]]:
    return db.get_all_products(limit=limit)


def get_offers_by_barcode(barcode: str) -> List[Dict[str, Any]]:
    return db.get_offers_by_barcode(barcode)


def get_similar_products(product: Dict[str, Any], limit: int = 6) -> List[Dict[str, Any]]:
    return db.get_similar_products(product=product, limit=limit)


def get_products_by_category(
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    exclude_barcode: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    return db.get_products_by_category(
        category=category,
        subcategory=subcategory,
        exclude_barcode=exclude_barcode,
        limit=limit,
    )


def get_product_count() -> int:
    return db.get_product_count()


def get_offer_count() -> int:
    return db.get_offer_count()


def seed_products_from_json() -> int:
    return db.seed_products_from_json()


def seed_startup_products() -> int:
    return db.seed_startup_products()


def seed_sample_offers() -> int:
    return db.seed_sample_offers()
