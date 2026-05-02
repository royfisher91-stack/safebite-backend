# SafeBite Phase 1 Batch Checklist

Use this before importing any controlled batch.

## Batch size

- One subcategory only
- 1 to 8 verified products
- Keep batches small until repeated validation stays clean

## Product rules

Every new product row must have:

- barcode / GTIN with a valid checksum
- name
- brand
- category
- subcategory
- ingredients
- GTIN source URL
- title / ingredients source URL

The importer blocks:

- duplicate barcodes already in `products`
- duplicate barcodes inside the batch
- placeholder barcodes
- mixed subcategories
- category or subcategory drift
- missing ingredients

## Offer rules

Every new product must have at least one offer row.

Every offer row must have:

- barcode
- retailer
- price
- stock status
- product URL

Allowed stock values for verified batches:

- `in_stock`
- `out_of_stock`

## Locked run order

```bash
cd /Users/royfisher/Desktop/product-safety-app/backend
.venv/bin/python scripts/import_verified_batch.py --db safebite.db --products imports/templates/products_batch_template.csv --offers imports/templates/offers_batch_template.csv
.venv/bin/python scripts/coverage_summary_report.py --db safebite.db
.venv/bin/python scripts/alternatives_quality_report.py --db safebite.db
.venv/bin/python scripts/validate_backend.py --db safebite.db
```

Then keep the existing live backend validation flow:

```bash
.venv/bin/python run_imports.py
.venv/bin/python coverage_summary_report.py
.venv/bin/python alternatives_quality_report.py
.venv/bin/python validate_backend.py
```

## Continue only if

- 0 warnings
- 0 errors
- no importer blocks
- no coverage issues
- no alternatives issues

## Locked future modules

Do not mix these into Phase 1 data batches:

- health condition profile expansion
- voucher or promo systems
- mobile feature work
- backend scoring engine upgrades
- recall layer
- barcode alias model
