# SafeBite Product Catalogue Volume Strategy

## Purpose

SafeBite needs enough product catalogue coverage for barcode scanning to feel useful at launch. Retailer prices and stock should stay verified and separate, but a product can still be useful when it has a valid barcode, name, ingredients, allergens, and source metadata.

This creates two data tracks:

1. **High-volume product catalogue**
   - Stores product identity and safety-relevant information.
   - Can use approved open or licensed catalogue sources, such as local Open Food Facts exports.
   - Does not require a retailer offer.

2. **Verified retailer offers/prices**
   - Stores retailer, price, stock, URL, and offer data.
   - Requires manual CSV, licensed feed, approved API, supplier feed, affiliate feed, or local business data.
   - Must remain separate from product safety scoring.

## Why Catalogue Products Can Exist Without Offers

A catalogue-only product can still support a useful scan result:

- product found
- ingredients shown
- allergens shown
- safety analysis available where data is sufficient
- alternatives available where the catalogue has comparable products
- retailer offers shown as empty when none are verified

The UI should present missing retailer coverage plainly, for example: "No verified retailer offer yet."

## Open Catalogue Source Rules

Open Food Facts or another approved open/licensed product dataset may be used for catalogue growth only when imported from a local CSV or JSONL file. Large imports must not hammer public APIs.

Open Food Facts data is community-sourced, so SafeBite must not treat it as equivalent to manufacturer, retailer, or manually verified data. Imported rows should be marked with:

- `source=open_food_facts`
- `data_confidence=community`
- `needs_manual_review=true` when ingredients or allergens are incomplete

Before production launch, TODO: confirm current dataset licence terms, attribution requirements, and legal wording.

## Retailer Offer Rules

Retailer offer data remains a higher-evidence track. Do not import prices, stock, or retailer URLs unless they come from:

- manual_csv
- licensed_feed
- approved_api
- supplier_feed
- affiliate_feed
- local_business

Do not scrape retailer websites. Do not guess price, stock, URL, or barcode data.

## Launch Targets

MVP catalogue target:

- 250+ products

Strong beta target:

- 500+ products

Retailer offer target:

- 50-100 verified retailer offers

Core subcategory target:

- 25+ Baby Meals
- 25+ Porridge
- 25+ Fruit Puree
- 25+ Formula Milk
- 25+ Snacks

## Validation Gates

Catalogue products may be promoted only when they are `safety_ready`:

- barcode exists
- GTIN/EAN checksum passes
- product name exists
- category and subcategory exist
- source exists
- source URL exists when available
- ingredients are present
- allergens are present or explicitly marked `none_declared`
- barcode is not duplicated in the staged file
- barcode does not already exist in live products

Rows with incomplete safety data stay staged as `needs_review`.

Rows with malformed or duplicate identity data are `rejected`.

## Promotion Rules

- Promote only `safety_ready` rows.
- Add product rows only.
- Do not create retailer offers from catalogue imports.
- Do not overwrite better verified data with weaker community data.
- Keep retailer offers as an empty list when none exist.
- Keep the Baby Meals verified source workflow for high-confidence retailer/manufacturer-backed rows.

## Risk Controls

- Community data is useful for coverage but may be incomplete or inconsistent.
- Source and confidence metadata must remain visible in reports.
- Product safety results must never be guessed.
- Catalogue imports must be reversible and batch-reviewed.
- Backend validation must remain at 0 warnings and 0 errors.
