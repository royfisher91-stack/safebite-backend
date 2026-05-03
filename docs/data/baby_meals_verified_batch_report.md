# SafeBite Baby Meals Verified Batch Report

Generated: 2026-05-03

## Source Workflow

Use `backend/imports/staged/baby_meals_source_queue.csv` to record source evidence before any live import. Example rows belong in review notes, not as fake CSV rows. A row can move to `verified` only when the GTIN, ingredients, allergens, price, and product URL are all backed by source URLs.

## Counts

- Baby Meals count before: 19
- Baby Meals count after: 19
- Products staged: 0
- Products verified: 0
- Products rejected: 0
- Offers staged: 0
- Offers verified: 0
- Offers rejected: 0
- Source rows: 6
- Source rows verified: 0
- Source rows needs_review: 6
- Source rows rejected: 0

## Blockers

- Duplicate barcodes: 0
- Duplicate barcode + retailer rows: 0
- Rows blocked due to checksum failure: 0
- Rows blocked due to missing ingredients: 0
- Rows blocked due to missing allergens: 0
- Rows blocked due to missing source URLs: 0
- Total blocked rows: 0
- Baby Meals reached 25+: no

## Validation Command Results

- `scripts/validate_baby_meals_verified_batch.py`: BLOCKED as expected; 6 needs_review rows, 0 verified rows, promotion threshold is 6
- `run_imports.py`: PASS; products 64, offers 104, validation issues 0, warnings 0, errors 0
- `coverage_summary_report.py`: PASS; issue_count 0
- `alternatives_quality_report.py`: PASS; issue_count 0
- `validate_backend.py`: PASS; products 64, validation warnings 0, validation errors 0

## Decision

BLOCKED

No live import was performed for this verified Baby Meals batch because the 6 candidate rows remain needs_review and have not been manually completed with GTIN, ingredient, allergen, and price evidence.

## Error Detail

- promotion requires at least 6 verified source-backed Baby Meals products; found 0
