# Baby Meals Batch 2 Rebuild Plan

Status: planning only. No products are added by this plan. No import or promotion is approved by this plan.

## Purpose

Baby Meals batch 2 is intended to be the first small, controlled product expansion batch after the Product Expansion Control Layer. The goal is to deepen the Baby & Toddler / Baby Meals subcategory without weakening SafeBite data quality or relying on local SQLite state.

Current locked baseline before any future Baby Meals batch 2 work:

- products: 97
- offers: 104
- Open Food Facts catalogue products restored: 33
- Open Food Facts catalogue products without retailer offers: 33

## Current Blocker

The old Baby Meals batch 2 candidate is blocked and must not be copied or imported as-is.

Known blockers from the audit:

- rows are marked `needs_review`
- GTIN/EAN checksum failures exist
- ingredients are `unknown`
- allergens are `unknown` for most rows
- product URLs are not manually verified

The rebuild must start from clean, source-backed values rather than the dirty old batch.

## Required Source Type

Allowed source type for this batch:

- `manual_csv`

No scraping-style uncontrolled sources are allowed.

## Required Future Files

Clean source file to create later, after verified data exists:

- `backend/imports/product_expansion/baby_meals_batch_2.csv`

Header-only template added now:

- `backend/imports/product_expansion/baby_meals_batch_2.template.csv`

Active batch plan to create later, only once real verified rows and exact deltas exist:

- `backend/imports/product_expansion/batch_plan.json`

Do not create the active batch plan until the batch data is complete and count deltas are known.

## Required Row Fields

Every row in the future clean CSV must include:

- `batch_id`
- `barcode`
- `product_name`
- `brand`
- `category`
- `subcategory`
- `ingredients`
- `allergens`
- `safety_notes`
- `retailer`
- `price`
- `promo_price`
- `stock_status`
- `product_url`
- `source_url`
- `last_verified_at`
- `manual_review_required`
- `review_reason`

## Barcode / GTIN Rules

- `barcode` must be present.
- Barcode must pass GTIN/EAN checksum validation.
- Barcode must not already exist in live products unless the batch is explicitly updating an existing product in a later approved workflow.
- Do not invent GTINs.
- Do not use retailer catalogue IDs as GTINs.
- Any checksum failure blocks the row.

## Ingredient Completeness Rules

- `ingredients` must be present for import-ready rows.
- `unknown`, blank, `data unavailable`, or equivalent values are not import-ready.
- Ingredients must be copied from source-backed evidence.
- Do not invent ingredients.
- If ingredients cannot be verified, set `manual_review_required` to `true` and keep the row blocked.

## Allergen Completeness Rules

- `allergens` must be present for import-ready rows.
- If allergens are declared, store them clearly, for example `milk`, `wheat; milk`, or `egg; milk`.
- If the source explicitly confirms no declared allergens, use `none_declared`.
- Do not use `none_declared` unless source evidence supports it.
- `unknown`, blank, `data unavailable`, or equivalent values are not import-ready.
- Do not invent allergens.
- If allergens cannot be verified, set `manual_review_required` to `true` and keep the row blocked.

## Retailer URL Verification Rules

- `product_url` must be present for every retailer-backed row.
- URL must start with `https://`.
- URL must point to the actual product page for the listed retailer.
- URL must be manually checked before the row is import-ready.
- Do not invent product URLs.

## Price Verification Rules

- `price` must be present and numeric for retailer-backed rows.
- `promo_price` may be blank when there is no verified promotion.
- Prices must come from source-backed evidence.
- Do not invent prices.
- If price cannot be verified, set `manual_review_required` to `true` and keep the row blocked.

## Stock-Status Rules

Allowed `stock_status` values:

- `in_stock`
- `out_of_stock`
- `unknown`

Use `unknown` unless stock is clearly confirmed. Unknown stock is allowed for retailer availability, but it must be explicit.

## Expected Delta Requirements

The active batch plan must declare exact expected count changes before any import:

- `expected_product_delta`
- `expected_offer_delta`
- `expected_products_without_retailer_offers_delta`

For Baby Meals batch 2, retailer offers are expected to be included, so:

- `retailer_offers_included` must be `true`
- `expected_offer_delta` must be greater than 0
- `expected_products_without_retailer_offers_delta` should be 0 unless a later approved plan says otherwise

## Manual Review Rules

Set `manual_review_required` to `true` when any of the following are true:

- barcode evidence is incomplete
- ingredients are incomplete
- allergens are incomplete
- product URL is not manually verified
- price is not manually verified
- row has conflicting source evidence

Rows with `manual_review_required=true` must not be promoted.

## Promotion Requirements

Promotion may be considered only after all of the following are true:

- clean CSV contains real source-backed rows
- active `batch_plan.json` exists with exact expected deltas
- `scripts/validate_product_expansion_plan.py` passes
- batch-specific validation passes with 0 errors
- fresh isolated DB validation is run before promotion
- product additions are reproducible from committed files only
- `scripts/validate_catalogue_reproducibility.py` passes
- `coverage_summary_report.py` has `issue_count: 0`
- `alternatives_quality_report.py` has `issue_count: 0`
- `validate_backend.py` passes with 0 warnings and 0 errors

## Rollback Requirements

If promotion is attempted later and any gate fails:

- stop immediately
- do not widen scope
- roll back only the selected batch changes
- restore expected counts to the last passing baseline
- keep the final decision blocked in the batch report

## Final Validation Gates

Before any future Baby Meals batch 2 promotion can be called complete, run:

```bash
./.venv/bin/python scripts/validate_product_expansion_plan.py
./.venv/bin/python scripts/validate_catalogue_reproducibility.py
./.venv/bin/python run_imports.py
./.venv/bin/python coverage_summary_report.py
./.venv/bin/python alternatives_quality_report.py
./.venv/bin/python validate_backend.py
```

Expected result before rows are added:

- products: 97
- offers: 104
- Open Food Facts catalogue products restored: 33
- Open Food Facts catalogue products without retailer offers: 33
- `validate_backend.py`: 0 warnings, 0 errors, PASS

## Current Decision

Baby Meals batch 2 remains planning-only and blocked until a clean source-backed CSV and active batch plan are created.
