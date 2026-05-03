import json
import re
import sqlite3
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlparse

from services.gtin_service import validate_gtin
from services.phase1_constants import ALLOWED_TAXONOMY, PLACEHOLDER_BARCODES
from services.phase2_import_normalization import build_name_key
from services.phase2_types import ProductImportRow, ValidationResult


_UNKNOWN_INGREDIENT_PATTERNS = [
    re.compile(r"\bflavourings?\b", re.IGNORECASE),
    re.compile(r"\bnatural flavours?\b", re.IGNORECASE),
    re.compile(r"\bspices?\b", re.IGNORECASE),
    re.compile(r"\bherbs?\b", re.IGNORECASE),
]

_SAMPLE_NAME_PATTERNS = [
    re.compile(r"\bsample\b", re.IGNORECASE),
    re.compile(r"\bplaceholder\b", re.IGNORECASE),
    re.compile(r"\btest product\b", re.IGNORECASE),
    re.compile(r"\bexample\b", re.IGNORECASE),
    re.compile(r"\bdemo\b", re.IGNORECASE),
]

_AUDIT_SOURCE = "phase2_existing_audit"
CATALOGUE_SOURCES = {"open_food_facts", "open_food_facts_catalogue", "licensed_catalogue"}


def _is_catalogue_source(value: Any) -> bool:
    return str(value or "").strip().lower() in CATALOGUE_SOURCES


class DuplicateDetector:
    def __init__(self) -> None:
        self._barcode_seen: Dict[str, str] = {}
        self._name_keys: Dict[str, str] = {}

    def check(self, row: ProductImportRow) -> List[Tuple[str, str]]:
        issues: List[Tuple[str, str]] = []

        if row.barcode:
            if row.barcode in self._barcode_seen:
                issues.append(("duplicate_barcode_in_batch", "Duplicate barcode found in current batch"))
            else:
                self._barcode_seen[row.barcode] = row.name

        name_key = build_name_key(row.name, row.brand)
        if name_key:
            if name_key in self._name_keys:
                previous_barcode = self._name_keys[name_key]
                if previous_barcode != row.barcode:
                    issues.append(("duplicate_name_in_batch", "Potential duplicate product name found in current batch"))
            else:
                self._name_keys[name_key] = row.barcode

        return issues


class FieldValidationEngine:
    ACCEPTABLE_BARCODE_LENGTHS = (8, 12, 13, 14)

    def __init__(
        self,
        db_path: Optional[str] = None,
        require_price: bool = True,
        check_database: bool = True,
        invalid_gtin_severity: str = "error",
        expect_nutrition: bool = True,
        expect_processing: bool = True,
    ) -> None:
        self.db_path = db_path
        self.require_price = require_price
        self.check_database = check_database
        self.invalid_gtin_severity = invalid_gtin_severity
        self.expect_nutrition = expect_nutrition
        self.expect_processing = expect_processing

    def validate_row(self, row: ProductImportRow) -> ValidationResult:
        result = ValidationResult(accepted=True)

        if not row.barcode:
            result.add_issue("missing_barcode", "error", "Missing barcode", "barcode")
        else:
            ok, detail = validate_gtin(row.barcode)
            if not ok:
                result.add_issue("invalid_barcode", self.invalid_gtin_severity, detail, "barcode")
            if is_placeholder_barcode(row.barcode):
                result.add_issue("placeholder_barcode", "error", "Placeholder barcode is not allowed", "barcode")
                result.add_flag("placeholder_barcode_flag")

        if not row.name:
            result.add_issue("missing_name", "error", "Missing product name", "name")
        elif any(pattern.search(row.name) for pattern in _SAMPLE_NAME_PATTERNS):
            result.add_issue("sample_like_name", "warning", "Name looks like a sample or example row", "name")
            result.add_flag("sample_name_flag")

        if not row.category:
            result.add_issue("missing_category", "error", "Missing category", "category")
        elif row.category not in ALLOWED_TAXONOMY:
            result.add_issue("category_outside_taxonomy", "error", "Category is outside locked taxonomy", "category")

        if not row.subcategory:
            result.add_issue("missing_subcategory", "error", "Missing subcategory", "subcategory")
        elif row.category in ALLOWED_TAXONOMY and row.subcategory not in ALLOWED_TAXONOMY[row.category]:
            result.add_issue("subcategory_outside_taxonomy", "error", "Subcategory is outside locked taxonomy", "subcategory")

        if self.require_price and row.price is None and row.promo_price is None:
            result.add_issue("missing_price_data", "error", "Missing price and promo price", "price")

        if row.product_url and not self._is_valid_url(row.product_url):
            result.add_issue("invalid_product_url", "error", "Invalid product URL", "product_url")

        if row.image_url and not self._is_valid_url(row.image_url):
            result.add_issue("invalid_image_url", "warning", "Invalid image URL", "image_url")

        self._apply_quality_flags(row, result)

        if self.db_path and self.check_database:
            self._check_against_database(row, result)

        result.accepted = not any(issue.severity == "error" for issue in result.issues)
        return result

    def _apply_quality_flags(self, row: ProductImportRow, result: ValidationResult) -> None:
        ingredients_text = row.ingredients or ""
        if ingredients_text:
            if any(pattern.search(ingredients_text) for pattern in _UNKNOWN_INGREDIENT_PATTERNS):
                result.add_flag("unknown_ingredient_flag")
        else:
            result.add_flag("missing_ingredients_flag")

        if self.expect_nutrition and not row.nutrition_json:
            result.add_flag("missing_nutrition_flag")

        if self.expect_processing and not row.processing_notes:
            result.add_flag("missing_processing_flag")

    def _check_against_database(self, row: ProductImportRow, result: ValidationResult) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()

            if row.barcode:
                cursor.execute("SELECT barcode, name FROM products WHERE barcode = ?", (row.barcode,))
                existing = cursor.fetchone()
                if existing:
                    existing_barcode, existing_name = existing
                    if (existing_name or "").strip().lower() != (row.name or "").strip().lower():
                        result.add_issue(
                            "duplicate_barcode_in_database",
                            "warning",
                            "Barcode already exists in database with a different name",
                            "barcode",
                        )

            name_key = build_name_key(row.name, row.brand)
            if name_key:
                cursor.execute("SELECT barcode, name, brand FROM products")
                for existing_barcode, existing_name, existing_brand in cursor.fetchall():
                    existing_key = build_name_key(existing_name, existing_brand)
                    if existing_key and existing_key == name_key and existing_barcode != row.barcode:
                        result.add_issue(
                            "duplicate_name_in_database",
                            "warning",
                            "Potential duplicate product name found in database",
                            "name",
                        )
                        break
        finally:
            conn.close()

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        try:
            parsed = urlparse(url)
        except Exception:
            return False
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def is_placeholder_barcode(barcode: str) -> bool:
    barcode = str(barcode or "").strip()
    if barcode in PLACEHOLDER_BARCODES:
        return True
    if barcode.startswith("9000000000"):
        return True
    if barcode and len(set(barcode)) == 1:
        return True
    return False


def ensure_phase2_tables(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product_quality_flags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT NOT NULL,
                flag_name TEXT NOT NULL,
                retailer TEXT,
                source TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
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
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_quality_flags_barcode ON product_quality_flags(barcode)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_quality_flags_source ON product_quality_flags(source)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_import_validation_issues_barcode ON import_validation_issues(barcode)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_import_validation_issues_source ON import_validation_issues(source)")
        conn.commit()
    finally:
        conn.close()


def persist_validation_result(db_path: str, row: ProductImportRow, validation: ValidationResult) -> None:
    ensure_phase2_tables(db_path)
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM product_quality_flags
            WHERE barcode = ? AND source = ? AND (retailer = ? OR (retailer IS NULL AND ? IS NULL))
            """,
            (row.barcode, row.source, row.retailer, row.retailer),
        )
        cursor.execute(
            """
            DELETE FROM import_validation_issues
            WHERE barcode = ? AND source = ? AND (retailer = ? OR (retailer IS NULL AND ? IS NULL))
            """,
            (row.barcode, row.source, row.retailer, row.retailer),
        )

        for flag_name in validation.quality_flags:
            cursor.execute(
                """
                INSERT INTO product_quality_flags (barcode, flag_name, retailer, source)
                VALUES (?, ?, ?, ?)
                """,
                (row.barcode, flag_name, row.retailer, row.source),
            )

        for issue in validation.issues:
            cursor.execute(
                """
                INSERT INTO import_validation_issues (
                    barcode, product_name, code, severity, message, field_name, retailer, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row.barcode,
                    row.name,
                    issue.code,
                    issue.severity,
                    issue.message,
                    issue.field_name,
                    row.retailer,
                    row.source,
                ),
            )

        conn.commit()
    finally:
        conn.close()


def _columns(conn: sqlite3.Connection, table: str) -> Sequence[str]:
    return [row[1] for row in conn.execute("PRAGMA table_info({})".format(table)).fetchall()]


def _decode_text_list(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(str(item).strip() for item in value if str(item).strip())
    text = str(value).strip()
    if not text:
        return ""
    try:
        parsed = json.loads(text)
    except Exception:
        return text
    if isinstance(parsed, list):
        return "; ".join(str(item).strip() for item in parsed if str(item).strip())
    return text


def _decode_json_dict(value: Any) -> Optional[Dict[str, Any]]:
    if value in (None, ""):
        return None
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(value)
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) else None


def _active_price(row: sqlite3.Row) -> Optional[float]:
    promo = row["promo_price"] if "promo_price" in row.keys() else None
    price = row["price"] if "price" in row.keys() else None
    try:
        if promo is not None and float(promo) > 0:
            return float(promo)
    except (TypeError, ValueError):
        pass
    try:
        if price is not None and float(price) > 0:
            return float(price)
    except (TypeError, ValueError):
        pass
    return None


def _has_example_url(conn: sqlite3.Connection, barcode: str) -> bool:
    rows = conn.execute(
        "SELECT product_url FROM offers WHERE barcode = ?",
        (barcode,),
    ).fetchall()
    for row in rows:
        url = str(row["product_url"] or "").strip().lower()
        if "example" in url:
            return True
    return False


def refresh_existing_quality_records(db_path: str) -> Dict[str, int]:
    ensure_phase2_tables(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("DELETE FROM product_quality_flags WHERE source = ?", (_AUDIT_SOURCE,))
        conn.execute("DELETE FROM import_validation_issues WHERE source = ?", (_AUDIT_SOURCE,))
        conn.commit()

        product_columns = set(_columns(conn, "products"))
        expect_nutrition = "nutrition_json" in product_columns
        expect_processing = "processing_notes" in product_columns
        validator = FieldValidationEngine(
            db_path=None,
            require_price=False,
            check_database=False,
            invalid_gtin_severity="warning",
            expect_nutrition=expect_nutrition,
            expect_processing=expect_processing,
        )

        products = conn.execute(
            "SELECT * FROM products ORDER BY name COLLATE NOCASE"
        ).fetchall()

        product_count = 0
        for product in products:
            barcode = str(product["barcode"] or "").strip()
            row = ProductImportRow(
                barcode=barcode,
                name=str(product["name"] or "").strip(),
                brand=str(product["brand"] or "").strip(),
                category=str(product["category"] or "").strip(),
                subcategory=str(product["subcategory"] or "").strip(),
                ingredients=_decode_text_list(product["ingredients"]),
                allergens=_decode_text_list(product["allergens"]),
                nutrition_json=_decode_json_dict(product["nutrition_json"]) if "nutrition_json" in product.keys() else None,
                processing_notes=str(product["processing_notes"] or "").strip() if "processing_notes" in product.keys() else None,
                source=_AUDIT_SOURCE,
                source_retailer=str(product["source_retailer"] or "").strip(),
            )
            validation = validator.validate_row(row)

            if _has_example_url(conn, barcode):
                validation.add_issue("example_offer_url", "warning", "One or more offer URLs still look like sample/example data", "product_url")
                validation.add_flag("example_offer_url_flag")

            offer_count = conn.execute("SELECT COUNT(*) AS c FROM offers WHERE barcode = ?", (barcode,)).fetchone()["c"]
            if int(offer_count or 0) == 0 and not _is_catalogue_source(product["source"]):
                validation.add_issue("product_without_offer", "warning", "Product has no retailer offers", "offers")
                validation.add_flag("product_without_offer_flag")

            persist_validation_result(db_path, row, validation)
            product_count += 1

        offer_rows = conn.execute("SELECT * FROM offers ORDER BY id").fetchall()
        offer_count = 0
        for offer in offer_rows:
            active_price = _active_price(offer)
            url = str(offer["product_url"] or "").strip()
            row = ProductImportRow(
                barcode=str(offer["barcode"] or "").strip(),
                name="offer:{0}".format(offer["id"]),
                category="Baby & Toddler",
                subcategory="Baby Meals",
                price=active_price,
                retailer=str(offer["retailer"] or "").strip(),
                product_url=url,
                source=_AUDIT_SOURCE,
            )
            validation = ValidationResult(accepted=True)
            if active_price is None or active_price <= 0:
                validation.add_issue("invalid_offer_price", "error", "Offer has no valid price or promo price", "price")
            if not url.startswith(("http://", "https://")):
                validation.add_issue("invalid_offer_url", "error", "Offer URL is missing or invalid", "product_url")
            elif "example" in url.lower():
                validation.add_issue("example_offer_url", "warning", "Offer URL still looks like sample/example data", "product_url")
            validation.accepted = not any(issue.severity == "error" for issue in validation.issues)
            if validation.issues:
                persist_validation_result(db_path, row, validation)
            offer_count += 1

        return {"products_audited": product_count, "offers_audited": offer_count}
    finally:
        conn.close()
