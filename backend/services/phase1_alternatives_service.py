import sqlite3
from typing import Any, Dict, List, Optional


def safe_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def effective_price(offer: Dict[str, Any]) -> Optional[float]:
    promo = safe_float(offer.get("promo_price"))
    price = safe_float(offer.get("price"))
    return promo if promo is not None and promo > 0 else price


def db_connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_product_with_offers(conn: sqlite3.Connection, barcode: str) -> Optional[Dict[str, Any]]:
    product = conn.execute(
        """
        SELECT barcode, name, brand, category, subcategory,
               ingredients, allergens, safety_score, safety_result
        FROM products
        WHERE barcode = ?
        """,
        (barcode,),
    ).fetchone()
    if not product:
        return None

    offers = conn.execute(
        """
        SELECT retailer, price, promo_price, stock_status, in_stock, product_url
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
    ).fetchall()

    data = dict(product)
    data["offers"] = [dict(row) for row in offers]
    return data


def best_in_stock_offer(offers: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    candidates = []
    for offer in offers:
        price = effective_price(offer)
        if not price:
            continue
        if offer.get("in_stock") in (1, True) or offer.get("stock_status") == "in_stock":
            item = dict(offer)
            item["effective_price"] = price
            candidates.append(item)
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: item["effective_price"])[0]


def candidate_products(conn: sqlite3.Connection, base: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT barcode, name, brand, category, subcategory,
               ingredients, allergens, safety_score, safety_result
        FROM products
        WHERE barcode != ?
          AND category = ?
          AND subcategory = ?
        """,
        (base["barcode"], base["category"], base["subcategory"]),
    ).fetchall()

    products = []
    for row in rows:
        product = fetch_product_with_offers(conn, row["barcode"])
        if not product:
            continue
        product["best_offer"] = best_in_stock_offer(product.get("offers") or [])
        products.append(product)
    return products


def summarise_candidate(product: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    best = product.get("best_offer")
    if not best:
        return None
    return {
        "barcode": product.get("barcode"),
        "name": product.get("name"),
        "brand": product.get("brand"),
        "category": product.get("category"),
        "subcategory": product.get("subcategory"),
        "safety_score": product.get("safety_score"),
        "safety_result": product.get("safety_result"),
        "retailer": best.get("retailer"),
        "price": best.get("effective_price"),
        "product_url": best.get("product_url"),
        "stock_status": best.get("stock_status"),
    }


def build_alternatives(conn: sqlite3.Connection, barcode: str) -> Dict[str, Any]:
    base = fetch_product_with_offers(conn, barcode)
    if not base:
        return {"barcode": barcode, "error": "product not found"}

    base_best_offer = best_in_stock_offer(base.get("offers") or [])
    base_price = base_best_offer.get("effective_price") if base_best_offer else None
    base_score = int(base.get("safety_score") or 0)
    candidates = candidate_products(conn, base)

    safer = None
    cheaper = None
    same_category = None

    safer_candidates = [
        item for item in candidates
        if item.get("best_offer") and int(item.get("safety_score") or 0) > base_score
    ]
    if safer_candidates:
        safer = summarise_candidate(sorted(
            safer_candidates,
            key=lambda item: (-int(item.get("safety_score") or 0), item["best_offer"]["effective_price"]),
        )[0])

    if base_price is not None:
        cheaper_candidates = [
            item for item in candidates
            if item.get("best_offer") and item["best_offer"]["effective_price"] < base_price
        ]
        if cheaper_candidates:
            cheaper = summarise_candidate(sorted(
                cheaper_candidates,
                key=lambda item: (item["best_offer"]["effective_price"], -int(item.get("safety_score") or 0)),
            )[0])

    same_candidates = [item for item in candidates if item.get("best_offer")]
    if same_candidates:
        same_category = summarise_candidate(sorted(
            same_candidates,
            key=lambda item: (-int(item.get("safety_score") or 0), item["best_offer"]["effective_price"]),
        )[0])

    return {
        "barcode": base.get("barcode"),
        "name": base.get("name"),
        "category": base.get("category"),
        "subcategory": base.get("subcategory"),
        "base_safety_score": base_score,
        "base_best_offer": base_best_offer,
        "safer_option": safer,
        "cheaper_option": cheaper,
        "same_category_option": same_category,
    }
