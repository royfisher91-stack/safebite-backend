# SafeBite Product Expansion Candidate Audit

Status: audit only. No products were added. No candidate imports were run.

## Current Baseline

Worktree: `/Users/royfisher/Desktop/safebite-product-work`

Branch: `product-expansion-control-plane`

Baseline counts before this audit:

- products: 97
- offers: 104
- Open Food Facts catalogue products restored: 33
- Open Food Facts catalogue products without retailer offers: 33
- active product expansion batch: none

The Product Expansion Control Layer is installed and `validate_backend.py` includes the product expansion plan gate.

## Audit Scope

Candidate batches reviewed:

1. Baby Meals batch 2
2. Boots expansion
3. supermarket expansion

The clean worktree was used for the audit report. Candidate source files were only read from the original dirty worktree where they did not exist in the clean worktree. Nothing was moved, copied, staged, restored, deleted, imported, or promoted from the dirty worktree.

## Candidate 1: Baby Meals Batch 2

### Location

Only present in the original dirty worktree:

- `/Users/royfisher/Desktop/product-safety-app/backend/imports/staged/baby_meals_batch_2_products.csv`
- `/Users/royfisher/Desktop/product-safety-app/backend/imports/staged/baby_meals_batch_2_offers.csv`
- `/Users/royfisher/Desktop/product-safety-app/backend/scripts/validate_baby_meals_batch_2.py`
- `/Users/royfisher/Desktop/product-safety-app/backend/validate_baby_meals_batch_2.py`

The clean worktree does not contain these batch files.

### Observed Batch Shape

- staged product rows: 10
- staged offer rows: 10
- estimated product delta if corrected and approved: +10
- estimated offer delta if corrected and approved: +10
- retailer offers included: yes
- source type fit: likely `manual_csv`, which is allowed by the control layer

### Data Quality Findings

The staged rows are explicitly marked `needs_review`. Sampled rows show blockers including:

- barcode failed GTIN checksum
- ingredients are `unknown`
- allergens are `unknown` for most rows
- product URLs are not manually verified

The existing validator is appropriately strict and would block promotion in the current state.

### Risk Rating

High.

Reasons:

- The batch is small and isolated, which is good.
- However, current rows are not import-ready.
- GTIN/checksum failures and unknown safety fields are hard blockers.
- The files only exist in the dirty worktree, so copying them without a clean extraction step risks bringing unrelated local work into the product branch.

### Decision

Blocked for import now.

This is the best candidate to revisit first only after every row is independently corrected, source-backed, and converted into a clean committed batch plan with explicit expected deltas.

## Candidate 2: Boots Expansion

### Location

Only present in the original dirty worktree:

- `/Users/royfisher/Desktop/product-safety-app/backend/imports/bulk/boots/raw.csv`
- `/Users/royfisher/Desktop/product-safety-app/backend/imports/templates/boots_bulk_template.csv`
- `/Users/royfisher/Desktop/product-safety-app/backend/imports/retailer_adapters/boots_adapter.py`
- `/Users/royfisher/Desktop/product-safety-app/backend/scripts/import_boots_bulk.py`
- `/Users/royfisher/Desktop/product-safety-app/backend/scripts/validate_boots_expansion.py`
- `/Users/royfisher/Desktop/product-safety-app/backend/scripts/boots_coverage_report.py`

The clean worktree does not contain the Boots source/import files.

### Observed Batch Shape

- Boots raw CSV rows: 0 product rows; header only
- estimated product delta: 0 from current raw file
- estimated offer delta: 0 from current raw file
- retailer offers included: intended, but no rows exist yet
- source type fit: likely `manual_csv`, which is allowed by the control layer

### Data Quality Findings

The Boots work appears to be expansion scaffolding rather than a product batch. The raw CSV has only a header. The validator checks adapter registration, retailer aliases, templates, and scaffold presence, but there is no product volume to import yet.

### Risk Rating

High.

Reasons:

- No import-ready product rows exist.
- The work depends on uncommitted adapter/import/service changes in the dirty worktree.
- Boots expansion touches retailer support and import plumbing, which is broader than a first controlled product batch.

### Decision

Deferred.

Boots should become its own clean foundation PR before any Boots product import. It is not suitable as the first product-expansion batch from the current clean baseline.

## Candidate 3: Supermarket Expansion

### Location

Partially present in the clean worktree as existing coverage/reporting code:

- `/Users/royfisher/Desktop/safebite-product-work/backend/scripts/supermarket_coverage_report.py`
- `/Users/royfisher/Desktop/safebite-product-work/backend/services/supermarket_coverage_service.py`

Additional candidate files only exist in the original dirty worktree:

- `/Users/royfisher/Desktop/product-safety-app/backend/imports/templates/supermarket_bulk_template.csv`
- `/Users/royfisher/Desktop/product-safety-app/backend/imports/iceland/raw.csv`
- `/Users/royfisher/Desktop/product-safety-app/backend/imports/ocado/raw.csv`
- `/Users/royfisher/Desktop/product-safety-app/backend/imports/waitrose/raw.csv`
- `/Users/royfisher/Desktop/product-safety-app/backend/scripts/validate_supermarket_expansion.py`

### Observed Batch Shape

- Iceland raw CSV rows: 0 product rows; header only
- Ocado raw CSV rows: 0 product rows; header only
- Waitrose raw CSV rows: 0 product rows; header only
- estimated product delta: 0 from current raw files
- estimated offer delta: 0 from current raw files
- retailer offers included: intended, but no rows exist yet
- source type fit: likely `manual_csv`, `licensed_feed`, `approved_api`, `affiliate_feed`, or `supplier_feed`, all allowed by the control layer

### Data Quality Findings

The supermarket expansion materials are scaffolding and header-only raw files. The candidate does not currently contain import-ready product data. The dirty worktree also includes modifications to shared import/reporting files, so moving this work into the clean branch would need a separate scoped PR.

### Risk Rating

Medium to High.

Reasons:

- No product rows exist yet, so there is no immediate data-quality risk from the files themselves.
- The implementation risk is higher because the dirty worktree contains shared importer/reporting changes.
- It is broader than a single product batch and should not be mixed with Baby Meals or Boots work.

### Decision

Deferred.

Supermarket expansion should be handled after a clean source batch exists for one retailer/category and after any required importer/reporting changes are separated from unrelated dirty work.

## Recommendation

No candidate is approved for import now.

Recommended first candidate for a future planned import: Baby Meals batch 2, but only after it is rebuilt as a clean source-backed batch.

Reasons:

- It is the smallest and most isolated candidate by scope.
- It has clear product and offer CSV boundaries.
- Expected movement is easy to define if corrected: approximately +10 products and +10 offers.
- It fits the new Product Expansion Control Layer as a `manual_csv` batch.

Current blockers before Baby Meals batch 2 can proceed:

- Correct or replace every failed GTIN.
- Replace `unknown` ingredients with source-backed values.
- Replace `unknown` allergens with source-backed values or a supported explicit `none_declared` value.
- Manually verify product URLs and prices.
- Move only the intended batch files into the clean worktree through a new branch/PR.
- Add an active `imports/product_expansion/batch_plan.json` with exact expected deltas.
- Run the product expansion plan validator before import.

## Next Required Step

Create a clean planning pass for Baby Meals batch 2 only. That pass should not import products. It should produce:

- a corrected source-backed product CSV
- a corrected source-backed offer CSV
- an active product expansion batch plan
- an expected count delta before import
- a validation report proving the batch is ready or blocked

Only after that should a controlled import be considered.

## Final Audit Decision

- products added: 0
- offers added: 0
- candidate imports run: none
- candidate promoted: none
- original dirty worktree touched: no edits; read-only source/status inspection only
