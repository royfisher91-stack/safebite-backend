import csv
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from services.analysis_service import analyse_product
from services.gtin_service import normalise_barcode, validate_gtin
from services.phase1_constants import (
    ALLOWED_TAXONOMY,
    CATEGORY_ALIASES,
    PLACEHOLDER_BARCODES,
    REQUIRED_OFFER_FIELDS,
    REQUIRED_PRODUCT_FIELDS,
    SUBCATEGORY_ALIASES,
    VALID_RETAILERS,
    VALID_STOCK_STATUSES,
)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def clean_lower(value: Any) -> str:
    return clean_text(value).lower()


def canonicalise_category(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return ""
    return CATEGORY_ALIASES.get(text.lower(), text)


def canonicalise_subcategory(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return ""
    return SUBCATEGORY_ALIASES.get(text.lower(), text)


def default_category_for_subcategory(subcategory: str) -> str:
    for category, subcategories in ALLOWED_TAXONOMY.items():
        if subcategory in subcategories:
            return category
    return ""


def enforce_taxonomy(category: Any, subcategory: Any) -> Tuple[str, str]:
    category_text = canonicalise_category(category)
    subcategory_text = canonicalise_subcategory(subcategory)

    if subcategory_text:
        forced_category = default_category_for_subcategory(subcategory_text)
        if forced_category:
            return forced_category, subcategory_text

    if category_text not in ALLOWED_TAXONOMY:
        return "", ""

    if subcategory_text not in ALLOWED_TAXONOMY[category_text]:
        return category_text, ""

    return category_text, subcategory_text


def parse_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [clean_text(item) for item in value if clean_text(item)]

    raw = clean_text(value)
    if not raw:
        return []

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [clean_text(item) for item in parsed if clean_text(item)]
    except Exception:
        pass

    parts = raw.replace("|", ";").split(";")
    if len(parts) == 1:
        parts = raw.split(",")
    return [part.strip() for part in parts if part.strip()]


def safe_float(value: Any) -> Optional[float]:
    raw = clean_text(value).replace("GBP", "").replace("\u00a3", "").replace(",", "")
    if not raw:
        return None
    try:
        return round(float(raw), 2)
    except (TypeError, ValueError):
        return None


def safe_optional_int(value: Any) -> Optional[int]:
    raw = clean_text(value)
    if not raw:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def load_csv_rows(path: str) -> List[Dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(path)
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def db_connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def barcode_exists(conn: sqlite3.Connection, barcode: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM products WHERE barcode = ? LIMIT 1",
        (barcode,),
    ).fetchone()
    return row is not None


def is_placeholder_barcode(barcode: str) -> bool:
    if barcode in PLACEHOLDER_BARCODES:
        return True
    if barcode.startswith("9000000000"):
        return True
    if len(set(barcode)) == 1:
        return True
    return False


def normalise_stock_status(value: Any) -> str:
    text = clean_lower(value).replace(" ", "_").replace("-", "_")
    if text in {"in_stock", "instock", "available", "true", "1", "yes"}:
        return "in_stock"
    if text in {"out_of_stock", "outofstock", "unavailable", "false", "0", "no"}:
        return "out_of_stock"
    return text


def normalise_product_row(row: Dict[str, Any]) -> Dict[str, Any]:
    category, subcategory = enforce_taxonomy(row.get("category"), row.get("subcategory"))
    ingredients = parse_list(row.get("ingredients"))
    allergens = parse_list(row.get("allergens"))

    return {
        "barcode": normalise_barcode(row.get("barcode", "")),
        "name": clean_text(row.get("name")),
        "brand": clean_text(row.get("brand")),
        "category": category,
        "subcategory": subcategory,
        "ingredients": ingredients,
        "allergens": allergens,
        "image_url": clean_text(row.get("image_url")),
        "source": clean_text(row.get("source")) or "manual_real_batch",
        "source_retailer": clean_text(row.get("source_retailer")) or "SafeBite Core Data",
        "description": clean_text(row.get("description")),
        "gtin_source_url": clean_text(row.get("gtin_source_url")),
        "title_source_url": clean_text(row.get("title_source_url")),
    }


def normalise_offer_row(row: Dict[str, Any]) -> Dict[str, Any]:
    price = safe_float(row.get("price"))
    promo_price = safe_float(row.get("promo_price"))
    stock_status = normalise_stock_status(row.get("stock_status"))
    buy_quantity = safe_optional_int(row.get("buy_quantity"))
    pay_quantity = safe_optional_int(row.get("pay_quantity"))
    bundle_price = safe_float(row.get("bundle_price"))

    return {
        "barcode": normalise_barcode(row.get("barcode", "")),
        "retailer": clean_text(row.get("retailer")),
        "price": price,
        "promo_price": promo_price,
        "original_price": safe_float(row.get("original_price")),
        "promo_text": clean_text(row.get("promo_text")),
        "promotion_type": clean_text(row.get("promotion_type")),
        "promotion_label": clean_text(row.get("promotion_label")),
        "buy_quantity": buy_quantity,
        "pay_quantity": pay_quantity,
        "bundle_price": bundle_price,
        "valid_from": clean_text(row.get("valid_from")),
        "valid_to": clean_text(row.get("valid_to")),
        "stock_status": stock_status,
        "in_stock": stock_status == "in_stock",
        "product_url": clean_text(row.get("product_url")),
        "image_url": clean_text(row.get("image_url")),
        "source": clean_text(row.get("source")) or clean_text(row.get("retailer")) or "manual_offer_batch",
        "source_retailer": clean_text(row.get("source_retailer")) or clean_text(row.get("retailer")),
    }


def validate_product_rows(
    conn: sqlite3.Connection,
    rows: List[Dict[str, Any]],
) -> Tuple[List[str], List[str], List[Dict[str, Any]]]:
    errors: List[str] = []
    warnings: List[str] = []
    cleaned: List[Dict[str, Any]] = []
    seen = set()

    if len(rows) > 8:
        errors.append("products.csv: batch has {0} products; keep controlled batches at 8 or fewer".format(len(rows)))

    for index, raw in enumerate(rows, start=2):
        row = normalise_product_row(raw)
        barcode = row["barcode"]

        missing = [field for field in REQUIRED_PRODUCT_FIELDS if not row.get(field)]
        if missing:
            errors.append("products.csv row {0}: missing required fields: {1}".format(index, ", ".join(missing)))
            continue

        ok, detail = validate_gtin(barcode)
        if not ok:
            errors.append("products.csv row {0}: {1} ({2})".format(index, detail, barcode))
            continue

        if is_placeholder_barcode(barcode):
            errors.append("products.csv row {0}: placeholder barcode is not allowed ({1})".format(index, barcode))
            continue

        if barcode in seen:
            errors.append("products.csv row {0}: duplicate barcode inside batch ({1})".format(index, barcode))
            continue
        seen.add(barcode)

        if barcode_exists(conn, barcode):
            errors.append("products.csv row {0}: barcode already exists in DB ({1})".format(index, barcode))
            continue

        if not row["category"] or not row["subcategory"]:
            errors.append("products.csv row {0}: category/subcategory is outside locked taxonomy".format(index))
            continue

        cleaned.append(row)

    subcategories = {row["subcategory"] for row in cleaned}
    if len(subcategories) > 1:
        errors.append("products.csv: batch mixes subcategories: {0}".format(", ".join(sorted(subcategories))))

    return errors, warnings, cleaned


def validate_offer_rows(
    conn: sqlite3.Connection,
    rows: List[Dict[str, Any]],
    product_rows: List[Dict[str, Any]],
) -> Tuple[List[str], List[str], List[Dict[str, Any]]]:
    errors: List[str] = []
    warnings: List[str] = []
    cleaned: List[Dict[str, Any]] = []
    product_barcodes = {row["barcode"] for row in product_rows}
    offers_seen = set()

    for index, raw in enumerate(rows, start=2):
        if not any(clean_text(value) for value in raw.values()):
            continue

        row = normalise_offer_row(raw)
        missing = [field for field in REQUIRED_OFFER_FIELDS if row.get(field) in (None, "")]
        if missing:
            errors.append("offers.csv row {0}: missing required fields: {1}".format(index, ", ".join(missing)))
            continue

        barcode = row["barcode"]
        retailer = row["retailer"]

        ok, detail = validate_gtin(barcode)
        if not ok:
            errors.append("offers.csv row {0}: {1} ({2})".format(index, detail, barcode))
            continue

        if retailer not in VALID_RETAILERS:
            errors.append("offers.csv row {0}: retailer is outside locked retailer set ({1})".format(index, retailer))
            continue

        if row["price"] is None or row["price"] <= 0:
            errors.append("offers.csv row {0}: price must be greater than 0".format(index))
            continue

        if row["promo_price"] is not None and row["promo_price"] <= 0:
            errors.append("offers.csv row {0}: promo_price must be greater than 0".format(index))
            continue

        if row["promo_price"] is not None and row["promo_price"] > row["price"]:
            errors.append("offers.csv row {0}: promo_price cannot be greater than price".format(index))
            continue

        if row["buy_quantity"] is not None and row["buy_quantity"] <= 1:
            errors.append("offers.csv row {0}: buy_quantity must be greater than 1 when provided".format(index))
            continue

        if row["pay_quantity"] is not None and row["buy_quantity"] is None:
            errors.append("offers.csv row {0}: pay_quantity requires buy_quantity".format(index))
            continue

        if (
            row["pay_quantity"] is not None
            and row["buy_quantity"] is not None
            and row["pay_quantity"] >= row["buy_quantity"]
            and row["bundle_price"] is None
        ):
            errors.append("offers.csv row {0}: pay_quantity must be lower than buy_quantity unless bundle_price is provided".format(index))
            continue

        if row["bundle_price"] is not None and row["bundle_price"] <= 0:
            errors.append("offers.csv row {0}: bundle_price must be greater than 0".format(index))
            continue

        if row["stock_status"] not in VALID_STOCK_STATUSES:
            errors.append("offers.csv row {0}: stock_status must be in_stock or out_of_stock".format(index))
            continue

        if not row["product_url"].startswith(("http://", "https://")):
            errors.append("offers.csv row {0}: product_url must start with http:// or https://".format(index))
            continue

        key = (barcode, retailer, row["product_url"])
        if key in offers_seen:
            errors.append("offers.csv row {0}: duplicate offer inside batch ({1}, {2})".format(index, barcode, retailer))
            continue
        offers_seen.add(key)

        if barcode not in product_barcodes and not barcode_exists(conn, barcode):
            errors.append("offers.csv row {0}: offer references barcode not present in batch or DB ({1})".format(index, barcode))
            continue

        cleaned.append(row)

    offered_barcodes = {row["barcode"] for row in cleaned}
    for product in product_rows:
        if product["barcode"] not in offered_barcodes:
            errors.append("offers.csv: new product has no offer in this batch ({0})".format(product["barcode"]))

    return errors, warnings, cleaned


def insert_product(conn: sqlite3.Connection, row: Dict[str, Any]) -> None:
    analysis = analyse_product(
        {
            "name": row["name"],
            "category": row["category"],
            "subcategory": row["subcategory"],
            "ingredients": row["ingredients"],
            "allergens": row["allergens"],
        }
    )

    conn.execute(
        """
        INSERT INTO products (
            barcode, name, brand, description, ingredients, allergens,
            category, subcategory, image_url, source, source_retailer,
            safety_score, safety_result, ingredient_reasoning, allergen_warnings,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        (
            row["barcode"],
            row["name"],
            row["brand"],
            row["description"],
            json.dumps(row["ingredients"], ensure_ascii=False),
            json.dumps(row["allergens"], ensure_ascii=False),
            row["category"],
            row["subcategory"],
            row["image_url"],
            row["source"],
            row["source_retailer"],
            analysis.get("safety_score"),
            analysis.get("safety_result"),
            analysis.get("ingredient_reasoning"),
            json.dumps(analysis.get("allergen_warnings") or [], ensure_ascii=False),
        ),
    )


def upsert_offer(conn: sqlite3.Connection, row: Dict[str, Any]) -> None:
    existing = conn.execute(
        """
        SELECT id
        FROM offers
        WHERE barcode = ? AND retailer = ?
        LIMIT 1
        """,
        (row["barcode"], row["retailer"]),
    ).fetchone()

    values = (
        row["price"],
        row["promo_price"],
        row["original_price"],
        row["promo_text"],
        row["promotion_type"],
        row["promotion_label"],
        row["buy_quantity"],
        row["pay_quantity"],
        row["bundle_price"],
        row["valid_from"],
        row["valid_to"],
        row["stock_status"],
        1 if row["in_stock"] else 0,
        row["product_url"],
        row["image_url"],
        row["source"],
        row["source_retailer"],
    )

    if existing:
        conn.execute(
            """
            UPDATE offers
            SET price = ?, promo_price = ?, original_price = ?, promo_text = ?,
                promotion_type = ?, promotion_label = ?, buy_quantity = ?, pay_quantity = ?,
                bundle_price = ?, valid_from = ?, valid_to = ?, stock_status = ?,
                in_stock = ?, product_url = ?, image_url = ?, source = ?,
                source_retailer = ?, last_seen = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            values + (existing["id"],),
        )
        return

    conn.execute(
        """
        INSERT INTO offers (
            barcode, retailer, price, promo_price, original_price, promo_text,
            promotion_type, promotion_label, buy_quantity, pay_quantity, bundle_price,
            valid_from, valid_to, stock_status, in_stock, product_url, image_url, source,
            source_retailer, last_seen, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        (
            row["barcode"],
            row["retailer"],
            row["price"],
            row["promo_price"],
            row["original_price"],
            row["promo_text"],
            row["promotion_type"],
            row["promotion_label"],
            row["buy_quantity"],
            row["pay_quantity"],
            row["bundle_price"],
            row["valid_from"],
            row["valid_to"],
            row["stock_status"],
            1 if row["in_stock"] else 0,
            row["product_url"],
            row["image_url"],
            row["source"],
            row["source_retailer"],
        ),
    )


def import_batch(
    db_path: str,
    products_csv: str,
    offers_csv: str,
) -> Tuple[List[str], List[str], Dict[str, int]]:
    conn = db_connect(db_path)
    try:
        product_rows = load_csv_rows(products_csv)
        offer_rows = load_csv_rows(offers_csv)

        product_errors, product_warnings, cleaned_products = validate_product_rows(conn, product_rows)
        offer_errors, offer_warnings, cleaned_offers = validate_offer_rows(conn, offer_rows, cleaned_products)

        errors = product_errors + offer_errors
        warnings = product_warnings + offer_warnings

        if errors or warnings:
            return errors, warnings, {"products_loaded": 0, "offers_upserted": 0}

        with conn:
            for row in cleaned_products:
                insert_product(conn, row)
            for row in cleaned_offers:
                upsert_offer(conn, row)

        return [], [], {
            "products_loaded": len(cleaned_products),
            "offers_upserted": len(cleaned_offers),
        }
    finally:
        conn.close()
