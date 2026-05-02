# SafeBite Phase 2 — Data Quality Hardening

This repo-specific Phase 2 layer adds import normalization helpers, duplicate detection, field validation, data quality flags, and a dedicated quality report without changing `mainBE.py` or the API architecture.

## Added files

- `services/phase2_types.py`
- `services/phase2_import_normalization.py`
- `services/phase2_data_quality.py`
- `services/phase2_reporting.py`
- `scripts/phase2_quality_report.py`
- `sql/phase2_sqlite_migration.sql`

## Database additions

The Phase 2 layer creates two audit tables when the report/import flow runs:

- `product_quality_flags`
- `import_validation_issues`

These are additive audit tables. They do not replace the current `products` or `offers` schema.

## Run order

From `backend`:

```bash
.venv/bin/python run_imports.py
.venv/bin/python scripts/coverage_summary_report.py --db safebite.db
.venv/bin/python scripts/alternatives_quality_report.py --db safebite.db
.venv/bin/python scripts/validate_backend.py --db safebite.db
.venv/bin/python scripts/phase2_quality_report.py --db safebite.db
```

## Important behavior

- Phase 1 validation remains the hard gate for the current controlled-batch workflow.
- Phase 2 reports existing weak rows as audit findings so they can be cleaned gradually.
- Missing nutrition and processing flags are only applied if those columns exist in the live schema. The current schema does not have them, so Phase 2 does not flood every row with irrelevant missing-field flags.
- Existing GTIN checksum issues are reported as warnings in Phase 2 audit mode, not hard failures, matching the deferred cleanup approach already used in Phase 1.

## Next cleanup target

The current expected weak rows are legacy/sample leftovers, especially:

- `500000000001` — Example Baby Oat Snack
- rows with `example` offer URLs
- deferred GTIN audit rows that need verified replacement or exception handling
