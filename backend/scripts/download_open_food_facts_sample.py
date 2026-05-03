#!/usr/bin/env python3
"""Download a modest Open Food Facts catalogue sample for SafeBite staging."""

import json
import sys
import time
import urllib.parse
import urllib.request
from urllib.error import HTTPError, URLError
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.gtin_service import normalise_barcode, validate_gtin  # noqa: E402


OUTPUT_PATH = ROOT / "imports" / "external" / "open_food_facts_sample.jsonl"
API_URL = "https://world.openfoodfacts.org/api/v2/search"
USER_AGENT = "SafeBite/1.0 (product-safety-app; contact-needed)"
PAGE_SIZE = 100
MAX_PRODUCTS = 250
REQUEST_SLEEP_SECONDS = 0.75
MAX_RETRIES = 3

CATEGORY_AREAS = [
    "baby-foods",
    "snacks-and-desserts-for-babies",
    "baby-cereals",
    "biscuits-for-babies",
    "baby-drinks",
    "infant-formulas",
    "fruit-purees",
    "breakfast-cereals",
    "yogurts",
    "milks",
]

FIELDS = [
    "code",
    "product_name",
    "brands",
    "categories",
    "categories_tags",
    "countries",
    "countries_tags",
    "ingredients_text",
    "ingredients_text_en",
    "allergens",
    "allergens_tags",
    "traces",
    "traces_tags",
    "url",
    "states_tags",
    "last_modified_t",
]

UK_MARKERS = {
    "uk",
    "gb",
    "england",
    "great britain",
    "united kingdom",
    "united-kingdom",
    "en:united-kingdom",
}


def _clean(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(str(item or "").strip() for item in value if str(item or "").strip())
    return str(value or "").strip()


def _is_uk_relevant(product: Dict[str, Any]) -> bool:
    text = "{} {}".format(_clean(product.get("countries")), _clean(product.get("countries_tags"))).lower()
    if not text:
        return True
    return any(marker in text for marker in UK_MARKERS)


def _has_ingredients(product: Dict[str, Any]) -> bool:
    return bool(_clean(product.get("ingredients_text")) or _clean(product.get("ingredients_text_en")))


def _product_url(category_tag: str, page: int) -> str:
    params = {
        "categories_tags_en": category_tag,
        "countries_tags_en": "united-kingdom",
        "fields": ",".join(FIELDS),
        "page_size": str(PAGE_SIZE),
        "page": str(page),
        "json": "1",
    }
    return "{}?{}".format(API_URL, urllib.parse.urlencode(params))


def _fetch_products(category_tag: str, page: int) -> List[Dict[str, Any]]:
    request = urllib.request.Request(
        _product_url(category_tag, page),
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )
    last_error = ""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
            products = payload.get("products") or []
            return [product for product in products if isinstance(product, dict)]
        except (HTTPError, URLError, TimeoutError) as exc:
            last_error = str(exc)
            time.sleep(REQUEST_SLEEP_SECONDS * attempt)
    print(
        "Warning: skipped search_terms={!r} page={} after API error: {}".format(
            category_tag,
            page,
            last_error,
        )
    )
    return []


def _passes_download_filters(product: Dict[str, Any]) -> bool:
    barcode = normalise_barcode(product.get("code"))
    valid_gtin, _message = validate_gtin(barcode)
    if not valid_gtin:
        return False
    if not _clean(product.get("product_name")):
        return False
    if not _has_ingredients(product):
        return False
    return True


def _write_jsonl(products: Iterable[Dict[str, Any]]) -> int:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with OUTPUT_PATH.open("w", encoding="utf-8") as handle:
        for product in products:
            handle.write(json.dumps(product, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def main() -> None:
    selected: List[Dict[str, Any]] = []
    selected_barcodes: Set[str] = set()
    downloaded = 0
    skipped_non_uk = 0
    skipped_incomplete = 0

    for category_tag in CATEGORY_AREAS:
        if len(selected) >= MAX_PRODUCTS:
            break
        for page in (1, 2):
            if len(selected) >= MAX_PRODUCTS:
                break
            products = _fetch_products(category_tag, page)
            downloaded += len(products)
            if not products:
                break

            for product in products:
                if len(selected) >= MAX_PRODUCTS:
                    break
                barcode = normalise_barcode(product.get("code"))
                if barcode in selected_barcodes:
                    continue
                if not _passes_download_filters(product):
                    skipped_incomplete += 1
                    continue

                if not _is_uk_relevant(product):
                    notes = _clean(product.get("safebite_download_notes"))
                    product["safebite_download_notes"] = "{}; UK relevance not explicit".format(notes).strip("; ")
                    skipped_non_uk += 1

                selected_barcodes.add(barcode)
                selected.append(product)

            time.sleep(REQUEST_SLEEP_SECONDS)

    written = _write_jsonl(selected)
    print("OPEN FOOD FACTS SAMPLE DOWNLOAD")
    print("=" * 80)
    print("Requests used category areas: {}".format(len(CATEGORY_AREAS)))
    print("Products returned by API: {}".format(downloaded))
    print("Products written: {}".format(written))
    print("Skipped incomplete/malformed: {}".format(skipped_incomplete))
    print("Rows with non-explicit UK relevance kept with notes: {}".format(skipped_non_uk))
    print("Output: {}".format(OUTPUT_PATH))


if __name__ == "__main__":
    main()
