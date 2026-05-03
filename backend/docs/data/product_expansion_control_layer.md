# SafeBite Product Expansion Control Layer

Status: active control layer for future product batches. No products are added by this document.

## Purpose

SafeBite product growth must be reproducible from committed files, auditable before import, and validated from a fresh isolated database. Product-count drift must not pass silently.

The locked baseline at the time this control layer was added is:

- products: 97
- offers: 104
- Open Food Facts catalogue products restored: 33
- Open Food Facts catalogue products without retailer offers: 33
- `validate_backend.py`: 0 warnings, 0 errors, PASS

## Batch Boundary Rules

Every product expansion branch must contain exactly one intentional product batch unless a planning report explicitly approves a combined batch.

Future candidate batches must be audited before implementation, including:

- Baby Meals batch 2
- Boots expansion
- supermarket expansion

Do not mix Baby Meals, Boots, supermarket, catalogue, dashboard, mobile, or unrelated backend work in the same product-expansion PR.

## Required Batch Declaration

Before promotion, each future batch must declare:

- `batch_id`
- `source_type`
- `source_file` or `source_files`
- `target_category`
- `target_subcategory`
- `expected_product_delta`
- `expected_offer_delta`
- `expected_products_without_retailer_offers_delta`
- `retailer_offers_included`
- `safety_fields_complete`
- `manual_review_required`

Allowed `source_type` values are:

- `manual_csv`
- `licensed_feed`
- `approved_api`
- `affiliate_feed`
- `supplier_feed`
- `catalogue_review`

Uncontrolled scraping-style sources are not allowed.

## Promotion Requirements

A product batch may only be promoted when all of the following are true:

- Expected product and offer deltas are declared before import.
- Source files are committed and referenced by the batch plan.
- Fresh isolated database validation is run before promotion.
- Product additions are reproducible from committed files only.
- No local SQLite-only product state is accepted.
- `scripts/validate_catalogue_reproducibility.py` passes.
- `validate_backend.py` passes with 0 warnings and 0 errors after promotion.
- Any expected count changes are updated in the same PR as the batch.

## Manual Review Rule

If safety fields are incomplete, `manual_review_required` must be `true` and the batch must not be treated as safety-ready without a later review gate.

## Retailer Offer Rule

Retailer offers remain separate from catalogue/safety data.

- If `retailer_offers_included` is `true`, `expected_offer_delta` must be greater than 0.
- If `retailer_offers_included` is `false`, `expected_offer_delta` must be 0.

## Validation Command

Run the product expansion plan validator before any future batch import:

```bash
./.venv/bin/python scripts/validate_product_expansion_plan.py
```

If no active batch exists, the validator should pass with:

```text
No active product expansion batch declared.
```

This pass state means product-expansion controls are installed. It does not approve any product import.
