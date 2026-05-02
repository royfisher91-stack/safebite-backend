# SafeBite Controlled Scaling System

This gate is for real product volume expansion only. It does not change app logic, routes, billing, frontend, mobile, `mainBE.py`, or product safety scoring.

Run from the backend folder:

```bash
./.venv/bin/python scripts/controlled_scaling_gate.py
```

Optional retailer-only gate:

```bash
./.venv/bin/python scripts/controlled_scaling_gate.py --retailer Tesco
```

## Batch Size Bands

- 100-250 rows
- 250-500 rows
- 500-1,000 rows

The gate allows smaller pilot batches, but any batch above 1,000 rows is blocked. Move to a larger band only after the previous band has:

- 0 errors
- 0 blocked rows
- 0 malformed rows
- 0 duplicates
- acceptable warnings
- passing validation and dry-run reports

## Gate Commands

The gate runs:

- `validate_real_product_batch.py`
- `import_category_batch.py --dry-run` for every non-empty active category CSV
- `product_volume_tracker.py`
- `bulk_import_quality_report.py`
- `supermarket_coverage_report.py`
- `validate_backend.py`

## Decision Output

The final output always includes:

- `safe to import: yes/no`
- `issues list`

Warnings are acceptable only when the validator passes and warning volume remains within the configured threshold. Missing ingredients/allergens must continue to mean safety is unknown or data unavailable; they must not create guessed safety results.
