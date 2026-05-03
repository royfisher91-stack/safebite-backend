import csv
import importlib
import json
import sqlite3
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from services.gtin_service import normalise_barcode, validate_gtin
from services.image_rights_service import normalise_image_metadata


DB_DEFAULT = str(Path(__file__).resolve().parents[1] / "safebite.db")

RETAILER_ALIASES = {
    "tesco": "Tesco",
    "asda": "Asda",
    "sainsburys": "Sainsbury's",
    "sainsbury's": "Sainsbury's",
    "sainsbury": "Sainsbury's",
    "waitrose": "Waitrose",
    "ocado": "Ocado",
    "iceland": "Iceland",
    "morrisons": "Morrisons",
    "morrison": "Morrisons",
    "m&s": "M&S",
    "marks and spencer": "M&S",
    "marks & spencer": "M&S",
    "marks_spencer": "M&S",
    "aldi": "Aldi",
    "lidl": "Lidl",
    "farmfoods": "Farmfoods",
    "home bargains": "Home Bargains",
    "home_bargains": "Home Bargains",
    "b&m": "B&M",
    "bm": "B&M",
    "b and m": "B&M",
    "heron": "Heron",
    "heron foods": "Heron",
}

ACTIVE_COVERAGE_RETAILERS = [
    "Tesco",
    "Asda",
    "Sainsbury's",
    "Waitrose",
    "Ocado",
    "Iceland",
    "Morrisons",
]

LATER_STAGE_RETAILERS = [
    "Aldi",
    "Lidl",
    "Farmfoods",
    "Home Bargains",
    "B&M",
    "Heron",
]

FUTURE_COMPATIBLE_RETAILERS = [
    "M&S",
] + LATER_STAGE_RETAILERS

ADAPTER_MODULES = {
    "Tesco": "imports.retailer_adapters.tesco_adapter",
    "Asda": "imports.retailer_adapters.asda_adapter",
    "Sainsbury's": "imports.retailer_adapters.sainsburys_adapter",
    "Waitrose": "imports.retailer_adapters.waitrose_adapter",
    "Ocado": "imports.retailer_adapters.ocado_adapter",
    "Iceland": "imports.retailer_adapters.iceland_adapter",
    "Morrisons": "imports.retailer_adapters.morrisons_adapter",
    "M&S": "imports.retailer_adapters.marks_spencer_adapter",
    "Aldi": "imports.retailer_adapters.aldi_adapter",
    "Lidl": "imports.retailer_adapters.lidl_adapter",
    "Farmfoods": "imports.retailer_adapters.farmfoods_adapter",
    "Home Bargains": "imports.retailer_adapters.home_bargains_adapter",
    "B&M": "imports.retailer_adapters.bm_adapter",
    "Heron": "imports.retailer_adapters.heron_adapter",
}


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalise_retailer(value: Any) -> str:
    text = clean_text(value)
    key = text.lower().replace("-", " ").strip()
    return RETAILER_ALIASES.get(key, text)


def parse_list_json(value: Any) -> str:
    if isinstance(value, list):
        return json.dumps([clean_text(item) for item in value if clean_text(item)], ensure_ascii=False)
    text = clean_text(value)
    if not text:
        return json.dumps([], ensure_ascii=False)
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return json.dumps([clean_text(item) for item in parsed if clean_text(item)], ensure_ascii=False)
    except Exception:
        pass
    text = text.replace("|", ";")
    parts = text.split(";") if ";" in text else text.split(",")
    return json.dumps([part.strip() for part in parts if part.strip()], ensure_ascii=False)


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, column_type: str) -> None:
    rows = conn.execute("PRAGMA table_info({0})".format(table)).fetchall()
    if column not in {row["name"] for row in rows}:
        conn.execute("ALTER TABLE {0} ADD COLUMN {1} {2}".format(table, column, column_type))


def ensure_phase12_schema(db_path: str = DB_DEFAULT) -> None:
    conn = _connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT UNIQUE,
                name TEXT,
                brand TEXT,
                category TEXT,
                subcategory TEXT,
                ingredients TEXT,
                allergens TEXT,
                image_url TEXT,
                image_source_type TEXT DEFAULT 'safebite_placeholder',
                image_rights_status TEXT DEFAULT 'not_required',
                image_credit TEXT,
                image_last_verified_at TIMESTAMP,
                source TEXT,
                data_quality_status TEXT DEFAULT 'unknown',
                last_verified_at TIMESTAMP
            )
            """
        )
        for column, column_type in [
            ("barcode", "TEXT"),
            ("name", "TEXT"),
            ("brand", "TEXT"),
            ("category", "TEXT"),
            ("subcategory", "TEXT"),
            ("ingredients", "TEXT"),
            ("allergens", "TEXT"),
            ("image_url", "TEXT"),
            ("image_source_type", "TEXT DEFAULT 'safebite_placeholder'"),
            ("image_rights_status", "TEXT DEFAULT 'not_required'"),
            ("image_credit", "TEXT"),
            ("image_last_verified_at", "TIMESTAMP"),
            ("source", "TEXT"),
            ("data_quality_status", "TEXT DEFAULT 'unknown'"),
            ("last_verified_at", "TIMESTAMP"),
            ("updated_at", "TIMESTAMP"),
        ]:
            _ensure_column(conn, "products", column, column_type)

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS retailer_offers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT NOT NULL,
                retailer TEXT NOT NULL,
                price REAL,
                promo_price REAL,
                multibuy_text TEXT,
                stock_status TEXT DEFAULT 'unknown',
                product_url TEXT,
                source TEXT,
                last_checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_retailer_offers_unique
            ON retailer_offers (barcode, retailer, product_url)
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_retailer_offers_barcode
            ON retailer_offers (barcode, retailer)
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS product_import_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                retailer TEXT,
                source_file TEXT,
                status TEXT,
                rows_total INTEGER DEFAULT 0,
                rows_imported INTEGER DEFAULT 0,
                rows_skipped INTEGER DEFAULT 0,
                errors_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS product_import_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id INTEGER,
                row_number INTEGER,
                retailer TEXT,
                barcode TEXT,
                reason TEXT,
                raw_row_preview TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_product_import_errors_batch
            ON product_import_errors (batch_id)
            """
        )
        conn.commit()
    finally:
        conn.close()


def load_adapter(retailer: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    canonical = normalise_retailer(retailer)
    module_name = ADAPTER_MODULES.get(canonical)
    if not module_name:
        raise ValueError("unsupported retailer: {0}".format(retailer))
    module = importlib.import_module(module_name)
    return module.adapt_row


def _row_preview(row: Dict[str, Any]) -> str:
    text = json.dumps(row, ensure_ascii=False, sort_keys=True)
    return text[:500]


def _data_quality_status(mapped: Dict[str, Any]) -> str:
    if mapped.get("name") and mapped.get("ingredients") and mapped.get("allergens"):
        return "verified"
    if mapped.get("name") or mapped.get("ingredients") or mapped.get("allergens"):
        return "partial"
    return "unknown"


def _validate_mapped_row(mapped: Dict[str, Any]) -> Tuple[bool, str]:
    barcode = normalise_barcode(mapped.get("barcode"))
    if not barcode:
        return False, "missing barcode"
    ok, detail = validate_gtin(barcode)
    if not ok:
        return False, detail
    if not mapped.get("name") and not mapped.get("price"):
        return False, "row has neither product name nor retailer offer price"
    return True, ""


def _upsert_product(conn: sqlite3.Connection, mapped: Dict[str, Any]) -> None:
    barcode = normalise_barcode(mapped.get("barcode"))
    image_metadata = normalise_image_metadata(mapped)
    values = {
        "barcode": barcode,
        "name": clean_text(mapped.get("name")),
        "brand": clean_text(mapped.get("brand")),
        "category": clean_text(mapped.get("category")),
        "subcategory": clean_text(mapped.get("subcategory")),
        "ingredients": parse_list_json(mapped.get("ingredients")),
        "allergens": parse_list_json(mapped.get("allergens")),
        "image_url": clean_text(mapped.get("image_url")),
        "image_source_type": image_metadata["image_source_type"],
        "image_rights_status": image_metadata["image_rights_status"],
        "image_credit": image_metadata["image_credit"],
        "image_last_verified_at": image_metadata["image_last_verified_at"],
        "source": clean_text(mapped.get("source")) or "phase12_bulk_import",
        "data_quality_status": _data_quality_status(mapped),
    }
    existing = conn.execute(
        """
        SELECT id, image_url, image_source_type, image_rights_status, image_credit, image_last_verified_at
        FROM products
        WHERE barcode = ?
        """,
        (barcode,),
    ).fetchone()
    if existing:
        has_image_update = bool(values["image_url"]) or any(
            clean_text(mapped.get(field))
            for field in [
                "image_source_type",
                "image_rights_status",
                "image_credit",
                "image_last_verified_at",
            ]
        )
        if not has_image_update:
            existing_metadata = normalise_image_metadata(dict(existing))
            values["image_source_type"] = existing_metadata["image_source_type"]
            values["image_rights_status"] = existing_metadata["image_rights_status"]
            values["image_credit"] = existing_metadata["image_credit"]
            values["image_last_verified_at"] = existing_metadata["image_last_verified_at"]
        conn.execute(
            """
            UPDATE products
            SET name = COALESCE(NULLIF(?, ''), name),
                brand = COALESCE(NULLIF(?, ''), brand),
                category = COALESCE(NULLIF(?, ''), category),
                subcategory = COALESCE(NULLIF(?, ''), subcategory),
                ingredients = CASE WHEN ? != '[]' THEN ? ELSE ingredients END,
                allergens = CASE WHEN ? != '[]' THEN ? ELSE allergens END,
                image_url = COALESCE(NULLIF(?, ''), image_url),
                image_source_type = ?,
                image_rights_status = ?,
                image_credit = ?,
                image_last_verified_at = ?,
                source = COALESCE(NULLIF(?, ''), source),
                data_quality_status = ?,
                last_verified_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE barcode = ?
            """,
            (
                values["name"],
                values["brand"],
                values["category"],
                values["subcategory"],
                values["ingredients"],
                values["ingredients"],
                values["allergens"],
                values["allergens"],
                values["image_url"],
                values["image_source_type"],
                values["image_rights_status"],
                values["image_credit"],
                values["image_last_verified_at"],
                values["source"],
                values["data_quality_status"],
                barcode,
            ),
        )
        return

    conn.execute(
        """
        INSERT INTO products (
            barcode, name, brand, category, subcategory, ingredients, allergens,
            image_url, image_source_type, image_rights_status, image_credit,
            image_last_verified_at, source, data_quality_status, last_verified_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            values["barcode"],
            values["name"],
            values["brand"],
            values["category"],
            values["subcategory"],
            values["ingredients"],
            values["allergens"],
            values["image_url"],
            values["image_source_type"],
            values["image_rights_status"],
            values["image_credit"],
            values["image_last_verified_at"],
            values["source"],
            values["data_quality_status"],
        ),
    )


def _upsert_retailer_offer(conn: sqlite3.Connection, mapped: Dict[str, Any], retailer: str) -> None:
    barcode = normalise_barcode(mapped.get("barcode"))
    product_url = clean_text(mapped.get("product_url"))
    conn.execute(
        """
        INSERT INTO retailer_offers (
            barcode, retailer, price, promo_price, multibuy_text, stock_status,
            product_url, source, last_checked_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(barcode, retailer, product_url)
        DO UPDATE SET
            price = excluded.price,
            promo_price = excluded.promo_price,
            multibuy_text = excluded.multibuy_text,
            stock_status = excluded.stock_status,
            source = excluded.source,
            last_checked_at = CURRENT_TIMESTAMP
        """,
        (
            barcode,
            retailer,
            mapped.get("price"),
            mapped.get("promo_price"),
            clean_text(mapped.get("multibuy_text")),
            clean_text(mapped.get("stock_status")) or "unknown",
            product_url,
            clean_text(mapped.get("source")) or "phase12_bulk_import",
        ),
    )


def _insert_batch(conn: sqlite3.Connection, retailer: str, source_file: str) -> int:
    cursor = conn.execute(
        """
        INSERT INTO product_import_batches (
            retailer, source_file, status, rows_total, rows_imported, rows_skipped, errors_count
        ) VALUES (?, ?, 'running', 0, 0, 0, 0)
        """,
        (retailer, source_file),
    )
    return int(cursor.lastrowid)


def _log_error(
    conn: sqlite3.Connection,
    batch_id: int,
    row_number: int,
    retailer: str,
    barcode: str,
    reason: str,
    row: Dict[str, Any],
) -> None:
    conn.execute(
        """
        INSERT INTO product_import_errors (
            batch_id, row_number, retailer, barcode, reason, raw_row_preview
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (batch_id, row_number, retailer, barcode, reason, _row_preview(row)),
    )


def import_retailer_csv(
    csv_path: str,
    retailer: str,
    db_path: str = DB_DEFAULT,
    dry_run: bool = False,
) -> Dict[str, Any]:
    ensure_phase12_schema(db_path)
    canonical = normalise_retailer(retailer)
    adapter = load_adapter(canonical)
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(csv_path)

    conn = _connect(db_path)
    summary = {
        "retailer": canonical,
        "source_file": str(path),
        "dry_run": dry_run,
        "batch_id": None,
        "rows_total": 0,
        "rows_imported": 0,
        "rows_skipped": 0,
        "errors_count": 0,
        "status": "complete",
        "errors": [],
    }
    try:
        with conn:
            batch_id = _insert_batch(conn, canonical, str(path))
            summary["batch_id"] = batch_id

            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                for row_number, raw_row in enumerate(reader, start=2):
                    if not any(clean_text(value) for value in raw_row.values()):
                        continue
                    summary["rows_total"] += 1
                    mapped = adapter(raw_row)
                    mapped["retailer"] = canonical
                    mapped["barcode"] = normalise_barcode(mapped.get("barcode"))

                    valid, reason = _validate_mapped_row(mapped)
                    if not valid:
                        summary["rows_skipped"] += 1
                        summary["errors_count"] += 1
                        summary["errors"].append("row {0}: {1}".format(row_number, reason))
                        _log_error(conn, batch_id, row_number, canonical, mapped.get("barcode", ""), reason, raw_row)
                        continue

                    if not dry_run:
                        _upsert_product(conn, mapped)
                        _upsert_retailer_offer(conn, mapped, canonical)
                    summary["rows_imported"] += 1

            status = "dry_run" if dry_run else "complete"
            conn.execute(
                """
                UPDATE product_import_batches
                SET status = ?, rows_total = ?, rows_imported = ?, rows_skipped = ?, errors_count = ?
                WHERE id = ?
                """,
                (
                    status,
                    summary["rows_total"],
                    summary["rows_imported"],
                    summary["rows_skipped"],
                    summary["errors_count"],
                    batch_id,
                ),
            )
            summary["status"] = status
        return summary
    except Exception:
        conn.execute(
            "UPDATE product_import_batches SET status = 'failed' WHERE id = ?",
            (summary["batch_id"],),
        )
        conn.commit()
        raise
    finally:
        conn.close()
