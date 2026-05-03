#!/usr/bin/env python3
"""Validate SafeBite product expansion batch plans before product imports."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PLAN_DIR = BACKEND_DIR / "imports" / "product_expansion"
EXAMPLE_PLAN = PLAN_DIR / "batch_plan.example.json"
ACTIVE_PLAN = PLAN_DIR / "batch_plan.json"
ALLOWED_SOURCE_TYPES = {
    "manual_csv",
    "licensed_feed",
    "approved_api",
    "affiliate_feed",
    "supplier_feed",
    "catalogue_review",
}
REQUIRED_FIELDS = [
    "batch_id",
    "source_type",
    "target_category",
    "target_subcategory",
    "expected_product_delta",
    "expected_offer_delta",
    "expected_products_without_retailer_offers_delta",
    "retailer_offers_included",
    "safety_fields_complete",
    "manual_review_required",
]
INTEGER_FIELDS = [
    "expected_product_delta",
    "expected_offer_delta",
    "expected_products_without_retailer_offers_delta",
]
BOOLEAN_FIELDS = [
    "retailer_offers_included",
    "safety_fields_complete",
    "manual_review_required",
]


class PlanError(RuntimeError):
    pass


def load_json(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except json.JSONDecodeError as exc:
        raise PlanError("{0} is not valid JSON: {1}".format(path, exc))

    if not isinstance(value, dict):
        raise PlanError("{0} must contain a JSON object".format(path))
    return value


def is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def add_error(errors: List[str], message: str) -> None:
    errors.append(message)


def source_paths(plan: Dict[str, Any], errors: List[str]) -> List[str]:
    has_source_file = "source_file" in plan
    has_source_files = "source_files" in plan

    if has_source_file and has_source_files:
        add_error(errors, "Use source_file or source_files, not both")
        return []

    if not has_source_file and not has_source_files:
        add_error(errors, "Missing source_file or source_files")
        return []

    if has_source_file:
        value = plan.get("source_file")
        if not is_non_empty_string(value):
            add_error(errors, "source_file must be a non-empty string")
            return []
        return [str(value).strip()]

    value = plan.get("source_files")
    if not isinstance(value, list) or not value:
        add_error(errors, "source_files must be a non-empty list")
        return []

    paths = []
    for index, item in enumerate(value):
        if not is_non_empty_string(item):
            add_error(errors, "source_files[{0}] must be a non-empty string".format(index))
            continue
        paths.append(str(item).strip())
    return paths


def validate_relative_paths(paths: List[str], require_existing: bool, errors: List[str]) -> None:
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_absolute():
            add_error(errors, "Source path must be repo-relative, not absolute: {0}".format(raw_path))
            continue
        if ".." in path.parts:
            add_error(errors, "Source path must not traverse parent directories: {0}".format(raw_path))
            continue
        if require_existing and not (BACKEND_DIR / path).exists():
            add_error(errors, "Active batch source file does not exist: {0}".format(raw_path))


def validate_plan(plan: Dict[str, Any], label: str, require_existing_sources: bool) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    messages: List[str] = []

    for field in REQUIRED_FIELDS:
        if field not in plan:
            add_error(errors, "{0}: missing required field {1}".format(label, field))

    for field in ["batch_id", "source_type", "target_category", "target_subcategory"]:
        if field in plan and not is_non_empty_string(plan.get(field)):
            add_error(errors, "{0}: {1} must be a non-empty string".format(label, field))

    source_type = str(plan.get("source_type") or "").strip()
    if source_type and source_type not in ALLOWED_SOURCE_TYPES:
        add_error(
            errors,
            "{0}: source_type {1!r} is not allowed".format(label, source_type),
        )

    for field in INTEGER_FIELDS:
        value = plan.get(field)
        if isinstance(value, bool) or not isinstance(value, int):
            add_error(errors, "{0}: {1} must be an integer".format(label, field))
        elif value < 0:
            add_error(errors, "{0}: {1} cannot be negative".format(label, field))

    for field in BOOLEAN_FIELDS:
        if field in plan and not isinstance(plan.get(field), bool):
            add_error(errors, "{0}: {1} must be true or false".format(label, field))

    paths = source_paths(plan, errors)
    validate_relative_paths(paths, require_existing_sources, errors)

    retailer_offers_included = plan.get("retailer_offers_included")
    expected_offer_delta = plan.get("expected_offer_delta")
    if isinstance(retailer_offers_included, bool) and isinstance(expected_offer_delta, int):
        if retailer_offers_included and expected_offer_delta <= 0:
            add_error(errors, "{0}: expected_offer_delta must be greater than 0 when retailer offers are included".format(label))
        if not retailer_offers_included and expected_offer_delta != 0:
            add_error(errors, "{0}: expected_offer_delta must be 0 when retailer offers are not included".format(label))

    safety_fields_complete = plan.get("safety_fields_complete")
    manual_review_required = plan.get("manual_review_required")
    if safety_fields_complete is False and manual_review_required is not True:
        add_error(errors, "{0}: manual_review_required must be true when safety fields are incomplete".format(label))

    products_without_offers_delta = plan.get("expected_products_without_retailer_offers_delta")
    product_delta = plan.get("expected_product_delta")
    if isinstance(products_without_offers_delta, int) and isinstance(product_delta, int):
        if products_without_offers_delta > product_delta:
            add_error(errors, "{0}: products-without-offers delta cannot exceed product delta".format(label))

    if not errors:
        messages.append("{0}: plan schema valid".format(label))
    return errors, messages


def validate_example_plan(errors: List[str]) -> None:
    if not EXAMPLE_PLAN.exists():
        add_error(errors, "Missing example batch plan: {0}".format(EXAMPLE_PLAN.relative_to(BACKEND_DIR)))
        return

    plan = load_json(EXAMPLE_PLAN)
    plan_errors, messages = validate_plan(plan, "example", require_existing_sources=False)
    errors.extend(plan_errors)
    for message in messages:
        print(message)


def validate_active_plan(errors: List[str]) -> None:
    if not ACTIVE_PLAN.exists():
        print("No active product expansion batch declared.")
        return

    plan = load_json(ACTIVE_PLAN)
    active = plan.get("active", True)
    if active is not True:
        plan_errors, messages = validate_plan(plan, "inactive batch", require_existing_sources=False)
        errors.extend(plan_errors)
        for message in messages:
            print(message)
        print("No active product expansion batch declared.")
        return

    plan_errors, messages = validate_plan(plan, "active batch", require_existing_sources=True)
    errors.extend(plan_errors)
    for message in messages:
        print(message)

    if not plan_errors:
        print("Active product expansion batch declared: {0}".format(plan.get("batch_id")))


def main() -> int:
    print("PRODUCT EXPANSION PLAN VALIDATION")
    print("=" * 80)

    errors: List[str] = []
    try:
        validate_example_plan(errors)
        validate_active_plan(errors)
    except PlanError as exc:
        add_error(errors, str(exc))

    print("\nValidation errors: {0}".format(len(errors)))
    for error in errors:
        print("ERROR: {0}".format(error))

    if errors:
        return 1

    print("Product expansion plan validation: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
