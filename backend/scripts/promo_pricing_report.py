import argparse
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import database as database_module
import services.promo_service as promo_service_module
from database import DatabaseManager


def _parse_datetime(value: Any) -> Optional[datetime]:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _label(row: dict[str, Any]) -> str:
    return "{code} | {code_type} | {discount_type} | {plan_scope}".format(
        code=row.get("code") or "",
        code_type=row.get("code_type") or "",
        discount_type=row.get("discount_type") or "",
        plan_scope=row.get("plan_scope") or "all",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Report SafeBite Phase 7 promo and pricing quality")
    parser.add_argument("--db", default="safebite.db", help="Path to SQLite DB")
    args = parser.parse_args()

    database_module.db = DatabaseManager(args.db)
    promo_service_module.db = database_module.db

    conn = database_module.db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM promo_codes ORDER BY created_at DESC, id DESC")
    promo_rows = [dict(row) for row in cursor.fetchall()]

    cursor.execute("SELECT * FROM offers ORDER BY updated_at DESC, id DESC")
    offer_rows = [dict(row) for row in cursor.fetchall()]
    conn.close()

    now = datetime.now(timezone.utc)
    active_promos = [row for row in promo_rows if bool(row.get("is_active"))]
    expired_promos = [
        row
        for row in promo_rows
        if _parse_datetime(row.get("expires_at")) is not None and _parse_datetime(row.get("expires_at")) <= now
    ]
    exhausted_promos = [
        row
        for row in promo_rows
        if row.get("usage_limit") is not None and int(row.get("usage_count") or 0) >= int(row.get("usage_limit") or 0)
    ]
    influencer_promos = [row for row in promo_rows if str(row.get("code_type") or "").strip().lower() == "influencer"]

    invalid_promo_rows = [
        row
        for row in promo_rows
        if not str(row.get("code") or "").strip()
        or not str(row.get("code_type") or "").strip()
        or not str(row.get("discount_type") or "").strip()
    ]

    offer_promo_rows = [
        row
        for row in offer_rows
        if row.get("promo_price") is not None or str(row.get("promotion_type") or "").strip()
    ]
    multi_buy_rows = [
        row
        for row in offer_rows
        if row.get("buy_quantity") is not None or row.get("bundle_price") is not None
    ]
    invalid_offer_promo_rows = [
        row
        for row in offer_rows
        if (
            row.get("bundle_price") is not None and not row.get("buy_quantity")
        ) or (
            row.get("buy_quantity") is not None
            and int(row.get("buy_quantity") or 0) <= 1
        ) or (
            row.get("pay_quantity") is not None
            and row.get("buy_quantity") is not None
            and int(row.get("pay_quantity") or 0) >= int(row.get("buy_quantity") or 0)
            and row.get("bundle_price") is None
        )
    ]

    code_type_counts: Counter[str] = Counter()
    discount_type_counts: Counter[str] = Counter()
    retailer_promo_counts: Counter[str] = Counter()
    promotion_type_counts: Counter[str] = Counter()

    for row in promo_rows:
        code_type_counts[str(row.get("code_type") or "").strip().lower()] += 1
        discount_type_counts[str(row.get("discount_type") or "").strip().lower()] += 1

    for row in offer_promo_rows:
        retailer_promo_counts[str(row.get("retailer") or "").strip()] += 1
        promotion_type_counts[str(row.get("promotion_type") or "promo_price").strip().lower()] += 1

    print("PHASE 7 PROMO / PRICING REPORT")
    print("=" * 80)
    print(f"Promo codes total: {len(promo_rows)}")
    print(f"Active promo codes: {len(active_promos)}")
    print(f"Expired promo codes: {len(expired_promos)}")
    print(f"Usage-exhausted promo codes: {len(exhausted_promos)}")
    print(f"Influencer promo codes: {len(influencer_promos)}")
    print(f"Invalid promo rows: {len(invalid_promo_rows)}")
    print(f"Offers with promo pricing: {len(offer_promo_rows)}")
    print(f"Offers with multi-buy metadata: {len(multi_buy_rows)}")
    print(f"Invalid offer promotion rows: {len(invalid_offer_promo_rows)}")

    print("\nPromo code type counts")
    if code_type_counts:
        for key, count in code_type_counts.most_common():
            print(f"- {key or 'unknown'}: {count}")
    else:
        print("- none")

    print("\nDiscount type counts")
    if discount_type_counts:
        for key, count in discount_type_counts.most_common():
            print(f"- {key or 'unknown'}: {count}")
    else:
        print("- none")

    print("\nRetailers with promotional offer rows")
    if retailer_promo_counts:
        for key, count in retailer_promo_counts.most_common():
            print(f"- {key or 'unknown'}: {count}")
    else:
        print("- none")

    print("\nPromotion type counts on offers")
    if promotion_type_counts:
        for key, count in promotion_type_counts.most_common():
            print(f"- {key or 'promo_price'}: {count}")
    else:
        print("- none")

    print("\nExpired promo codes")
    if expired_promos:
        for row in expired_promos[:10]:
            print(f"- {_label(row)}")
    else:
        print("- none")

    print("\nUsage-exhausted promo codes")
    if exhausted_promos:
        for row in exhausted_promos[:10]:
            print(f"- {_label(row)}")
    else:
        print("- none")

    print("\nInvalid promo rows")
    if invalid_promo_rows:
        for row in invalid_promo_rows[:10]:
            print(f"- {_label(row)}")
    else:
        print("- none")

    print("\nInvalid offer promotion rows")
    if invalid_offer_promo_rows:
        for row in invalid_offer_promo_rows[:10]:
            print(
                "- {barcode} | {retailer} | promotion_type={promotion_type} | buy_quantity={buy_quantity} | pay_quantity={pay_quantity} | bundle_price={bundle_price}".format(
                    barcode=row.get("barcode") or "",
                    retailer=row.get("retailer") or "",
                    promotion_type=row.get("promotion_type") or "",
                    buy_quantity=row.get("buy_quantity"),
                    pay_quantity=row.get("pay_quantity"),
                    bundle_price=row.get("bundle_price"),
                )
            )
    else:
        print("- none")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
