# SafeBite Bulk Product Intake

This intake flow stages product and retailer availability data before anything reaches the live `products` or `offers` tables.

Allowed sources:
- `manual_csv`
- `licensed_feed`
- `approved_api`
- `affiliate_feed`
- `supplier_feed`
- `local_business`

Blocked sources:
- scraping or unapproved scrape exports

Target retailers:
- Tesco
- Asda
- Sainsbury's
- Waitrose
- Ocado
- Iceland
- M&S
- Aldi
- Lidl
- Farmfoods
- Home Bargains
- B&M
- Heron

Stage a CSV:

```bash
./.venv/bin/python scripts/stage_bulk_product_intake.py \
  --csv imports/templates/bulk_product_intake_template.csv \
  --source-type manual_csv \
  --retailer Tesco \
  --source-name tesco_manual_batch
```

Review batches:

```bash
./.venv/bin/python scripts/bulk_product_intake_report.py
```

Dry-run promotion:

```bash
./.venv/bin/python scripts/promote_bulk_product_intake.py --batch-id 1
```

Apply promotion:

```bash
./.venv/bin/python scripts/promote_bulk_product_intake.py --batch-id 1 --apply
```

Rows with missing barcode, invalid GTIN, placeholder barcode, unsupported retailer, or blocked source type are rejected. Rows with missing ingredients, allergens, price, or URL stay staged with warnings until verified. Safety scoring only uses verified product fields; retailer availability is stored separately.
