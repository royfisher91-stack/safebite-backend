# SafeBite Phase 1 Verified Batch Workflow

This repo now has an adapted Phase 1 toolkit under `backend/scripts` and `backend/services`.

The toolkit is intentionally additive. It does not replace the existing root scripts and does not modify `mainBE.py`.

## What is enforced for new verified batches

- valid GTIN checksum
- no placeholder barcode
- no duplicate product barcode
- one subcategory per batch
- locked category/subcategory taxonomy
- ingredients required
- source evidence URLs required in the product CSV
- at least one offer per new product
- retailer, price, stock status and URL required for offers

## What is audited but not blocked yet

Existing product rows are not all guaranteed to have authoritative GTIN evidence yet. The Phase 1 validation script reports existing invalid GTIN checks as an audit count so they can be cleaned gradually without breaking the current live dataset.

From now on, new rows should use the stricter importer.

## Commands

```bash
cd /Users/royfisher/Desktop/product-safety-app/backend
.venv/bin/python scripts/import_verified_batch.py --db safebite.db --products imports/templates/products_batch_template.csv --offers imports/templates/offers_batch_template.csv
.venv/bin/python scripts/coverage_summary_report.py --db safebite.db
.venv/bin/python scripts/alternatives_quality_report.py --db safebite.db
.venv/bin/python scripts/validate_backend.py --db safebite.db
```

Also keep running the original locked validation flow after data changes:

```bash
.venv/bin/python run_imports.py
.venv/bin/python coverage_summary_report.py
.venv/bin/python alternatives_quality_report.py
.venv/bin/python validate_backend.py
```
