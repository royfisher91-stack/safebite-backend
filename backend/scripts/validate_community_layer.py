import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import database as database_module
import services.community_service as community_service_module
from database import DatabaseManager, get_all_products
from services.analysis_service import analyse_product
from services.community_service import (
    COMMENT_MAX_LENGTH,
    build_feedback_summary,
    create_feedback,
    delete_feedback,
    flag_feedback,
    list_feedback,
)


def expect(condition: bool, message: str, failures: list[str]) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {message}")
    if not condition:
        failures.append(message)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SafeBite Phase 6 community layer")
    parser.add_argument("--db", default="safebite.db", help="Path to SQLite DB")
    args = parser.parse_args()

    database_module.db = DatabaseManager(args.db)
    community_service_module.db = database_module.db

    products = get_all_products()
    if not products:
        print("No products available for community validation.")
        return 1

    product = products[0]
    barcode = str(product.get("barcode") or "").strip()
    product_name = str(product.get("name") or "Unknown product").strip()

    failures: list[str] = []
    created_ids: list[int] = []

    before_analysis = analyse_product(product)

    try:
        positive = create_feedback(
            barcode=barcode,
            product_name=product_name,
            feedback_type="positive",
            comment="Worked well for our routine.",
            allergy_tags=["dairy"],
            condition_tags=[],
        )
        negative = create_feedback(
            barcode=barcode,
            product_name=product_name,
            feedback_type="negative",
            comment="This caused a reaction for us.",
            allergy_tags=["dairy"],
            condition_tags=["ibs"],
        )
        created_ids.extend([positive.get("id"), negative.get("id")])

        listed = list_feedback(barcode=barcode, limit=10)
        summary = build_feedback_summary(barcode)

        expect(len(listed) >= 2, "Community feedback list should return saved rows", failures)
        expect(
            summary.get("positive_count", 0) >= 1 and summary.get("negative_count", 0) >= 1,
            "Community summary should count positive and negative feedback separately",
            failures,
        )
        expect(
            summary.get("allergy_tag_counts", {}).get("dairy", 0) >= 2,
            "Community summary should aggregate allergy tag counts",
            failures,
        )
        expect(
            summary.get("condition_tag_counts", {}).get("ibs", 0) >= 1,
            "Community summary should aggregate condition tag counts",
            failures,
        )
        expect(
            all(item.get("feedback_type") in {"positive", "negative"} for item in listed[:2]),
            "Community list should keep structured feedback types",
            failures,
        )

        flagged = flag_feedback(int(negative["id"]), reason="validation smoke test")
        expect(flagged is not None, "Flagging community feedback should succeed", failures)

        after_flag_list = list_feedback(barcode=barcode, limit=10)
        expect(
            all(int(item.get("id") or 0) != int(negative["id"]) for item in after_flag_list),
            "Flagged community feedback should be excluded from the public list",
            failures,
        )

        after_analysis = analyse_product(product)
        expect(
            before_analysis.get("safety_score") == after_analysis.get("safety_score"),
            "Community feedback must not change the core safety score",
            failures,
        )
        expect(
            before_analysis.get("safety_result") == after_analysis.get("safety_result"),
            "Community feedback must not change the core safety result",
            failures,
        )
        expect(COMMENT_MAX_LENGTH == 280, "Comment length guard should stay locked at 280 characters", failures)
    finally:
        for feedback_id in created_ids:
            if feedback_id:
                delete_feedback(int(feedback_id))

    if failures:
        print("\nCommunity layer validation: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nCommunity layer validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
