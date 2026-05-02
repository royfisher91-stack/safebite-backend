# SafeBite Product Volume Status

This tracker is read-only. It measures product volume, retailer coverage, and import-batch health without changing app logic, safety scoring, billing, frontend, mobile, or backend routes.

Run from the backend folder:

```bash
./.venv/bin/python scripts/product_volume_tracker.py
./.venv/bin/python scripts/product_volume_tracker.py --write-markdown ../docs/data/product_volume_status.md
```

## Current Snapshot

- Database: `/Users/royfisher/Desktop/product-safety-app/backend/safebite.db`
- Total products: 64
- Total legacy offers: 104
- Total retailer_offers: 104
- Combined availability footprint: 208
- Missing ingredients: 0
- Missing allergens: 27
- Unknown stock rows: 0
- Missing URL rows: 0

## Products Per Category

| Category | Subcategory | Products |
| --- | --- | --- |
| Baby & Toddler | Toddler Milk | 2 |
| Baby & Toddler | Toddler Yoghurt | 2 |
| Baby Snacks | Baby Crisps & Puffs | 2 |
| Baby Snacks | Oat Snacks | 2 |
| Baby & Toddler | Fruit Puree | 11 |
| Baby & Toddler | Porridge | 12 |
| Baby & Toddler | Formula Milk | 14 |
| Baby & Toddler | Baby Meals | 19 |

## Retailer Coverage

| Retailer | Phase | Offer rows | Distinct products | Product coverage % |
| --- | --- | --- | --- | --- |
| Aldi | future-compatible | 0 | 0 | 0.0 |
| Asda | active | 32 | 16 | 25.0 |
| B&M | future-compatible | 0 | 0 | 0.0 |
| Farmfoods | future-compatible | 0 | 0 | 0.0 |
| Heron | future-compatible | 0 | 0 | 0.0 |
| Home Bargains | future-compatible | 0 | 0 | 0.0 |
| Iceland | active | 0 | 0 | 0.0 |
| Lidl | future-compatible | 0 | 0 | 0.0 |
| M&S | future-compatible | 0 | 0 | 0.0 |
| Morrisons | active | 0 | 0 | 0.0 |
| Ocado | active | 0 | 0 | 0.0 |
| Sainsbury's | active | 66 | 33 | 51.6 |
| Tesco | active | 110 | 55 | 85.9 |
| Waitrose | active | 0 | 0 | 0.0 |

## Retailer Offers Table

| Retailer | Retailer offer rows | Products |
| --- | --- | --- |
| Asda | 16 | 16 |
| Sainsbury's | 33 | 33 |
| Tesco | 55 | 55 |

## Product Retailer Spread

- 0 retailers: 0
- 1 retailer: 33
- 2-3 retailers: 31
- 4+ retailers: 0

## Batch Import Stats

Phase 12 retailer importer:

- Batch count: 13
- Rows total: 304
- Rows imported: 304
- Rows skipped: 0
- Errors count: 0
- Logged product_import_errors rows: 0

| Retailer | Status | Batches | Rows | Imported | Skipped | Errors |
| --- | --- | --- | --- | --- | --- | --- |
| Asda | complete | 1 | 16 | 16 | 0 | 0 |
| Asda | dry_run | 1 | 16 | 16 | 0 | 0 |
| Sainsbury's | complete | 1 | 33 | 33 | 0 | 0 |
| Sainsbury's | dry_run | 1 | 33 | 33 | 0 | 0 |
| Tesco | complete | 7 | 104 | 104 | 0 | 0 |
| Tesco | dry_run | 2 | 102 | 102 | 0 | 0 |

Controlled staging intake:

- Batch count: 3
- Rows total: 100
- Accepted rows: 100
- Rejected rows: 0
- Warnings: 0
- Errors: 0

| Status | Batches | Rows | Accepted | Rejected | Warnings | Errors |
| --- | --- | --- | --- | --- | --- | --- |
| staged | 3 | 100 | 100 | 0 | 0 | 0 |

## Recommendations

- Weakest category: Baby & Toddler / Toddler Milk (2 product(s))
- Weakest active retailer: Iceland (0 distinct product(s), 0 offer row(s))
- Next batch priority: Prioritise a verified Baby & Toddler / Toddler Milk batch for Iceland. Keep using approved CSV/feed/API/manual sources only, and promote only after validation has zero errors, blocked rows, malformed rows, and duplicates.

Future-compatible retailers are tracked for readiness, but they are not treated as current phase blockers.
