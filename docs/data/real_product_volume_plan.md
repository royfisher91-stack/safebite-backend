# SafeBite Real Product Volume Expansion Master Plan

Status: controlled expansion plan. This document does not authorise scraping, guessed data, placeholder products, or promotion of unvalidated rows.

## Non-Negotiable Data Rules

- Use only these source types: `manual_csv`, `licensed_feed`, `approved_api`, `supplier_feed`, `affiliate_feed`, `local_business`.
- Do not scrape websites.
- Do not guess barcodes, ingredients, allergens, prices, stock, product URLs, image URLs, or source URLs.
- Do not create placeholder products.
- Do not overwrite stronger verified data with weaker data.
- Missing data must remain `unknown`, `data unavailable`, empty, or null according to the destination field.
- Product safety must never be guessed.
- Retailer offers can exist without full safety data.
- Retailer availability must stay separate from product safety scoring.
- Community feedback must not change safety scoring.
- All imports must pass validation before promotion.

## Target Categories

### SafeBite Food

Initial food expansion should focus on everyday, high-repeat purchase categories where barcode lookup and supermarket comparison have clear value:

- Baby & Toddler
- Baby Snacks
- Breakfast cereals
- Dairy and dairy alternatives
- Free-from foods
- Snacks
- Soft drinks and juices
- Ready meals
- Cooking sauces and meal kits
- Frozen food
- Household pantry staples

### Future SafeHome Separation

SafeHome data must remain separate from SafeBite food safety data and scoring. SafeHome expansion can use the same intake discipline, but it must use separate rules, modules, reports, and validation:

- Household cleaning
- Laundry
- Dishwasher
- Surface cleaners
- Bathroom cleaners
- Kitchen cleaners
- Air care
- Pest control
- Child safety household items

SafeHome product availability may be staged before verified household hazard analysis exists, but the UI and API must show unknown or starter behaviour until verified SafeHome rules/data are available.

## Subcategory Priority

Priority 1: Baby & Toddler first

- Baby formula
- Baby meals
- Baby porridge
- Fruit puree
- Baby snacks
- Toddler yoghurt

Priority 2: Allergy-sensitive food categories

- Free-from bread and bakery
- Free-from snacks
- Dairy-free milk alternatives
- Gluten-free cereals
- Nut-containing and nut-free snack ranges

Priority 3: High-frequency supermarket comparison categories

- Cereals
- Yoghurts
- Drinks
- Ready meals
- Frozen meals
- Pasta sauces
- Pantry staples

Priority 4: SafeHome starter structure only

- Household cleaning
- Laundry
- Dishwasher
- Surface cleaners

## Retailer Priority Tiers

Core retailers:

1. Tesco
2. Asda
3. Sainsbury's
4. Waitrose
5. Ocado
6. Morrisons
7. M&S

Extended retailers:

1. Iceland
2. Aldi
3. Lidl
4. Farmfoods
5. Home Bargains
6. B&M
7. Heron

Expansion should start with core retailers, then add extended retailers when approved product access is available. Extended retailers must not create blockers merely because they have no current coverage.

## Batch Size Scaling Strategy

Stage 1: proof batches

- 10 to 25 rows per retailer/category file.
- One category at a time.
- Manual review required before promotion.

Stage 2: controlled category batches

- 50 to 100 rows per retailer/category file.
- Baby & Toddler remains the first large category.
- Compare duplicate rates and source quality before scaling.

Stage 3: category expansion

- 100 to 250 rows per batch.
- Only after validation and rollback process has been proven on smaller batches.
- Keep each batch retailer/category specific.

Stage 4: feed/API batches

- 250 to 1,000 rows per batch only for licensed feeds, approved APIs, supplier feeds, or affiliate feeds with stable schemas.
- No auto-promotion without validation and review.

Stage 5: large-volume operations

- Thousands of rows may be staged only after historical validation is clean and rollback is tested.
- Split by retailer, category, and source date.
- Promotion should be reversible at batch level.

## Validation Gates

Every staged batch must pass:

- CSV header validation.
- GTIN/EAN checksum validation.
- Required barcode validation.
- Required product name validation.
- Approved retailer validation.
- Approved category/subcategory validation.
- Approved source type validation.
- Stock status validation: `in_stock`, `out_of_stock`, or `unknown`.
- URL validation for product/source/image URLs when present.
- Duplicate `barcode + retailer` validation inside the batch.
- Malformed row detection.

Warnings, not errors:

- Missing ingredients.
- Missing allergens.

Missing ingredients/allergens must block guessed safety decisions, but they do not block retailer availability staging when the product and offer data are otherwise valid.

## Promotion Rules

- Promote only from validated staged files.
- Promote only rows with zero errors.
- Promotion must be explicit; dry-run output is not promotion.
- Promotion must record source type, source URL when available, retailer, category, subcategory, row count, skipped rows, and errors.
- A product row may update a product only when the incoming source is equal or stronger than existing verification quality.
- Availability/offer rows may be added when safety fields are incomplete, as long as this does not imply product safety.
- New product safety scoring must require verified ingredients/allergens/rules. If missing, safety remains unknown/data unavailable.

## Rollback Rules

- Every promotion must have a batch identifier.
- Rollback must be possible by batch, retailer, and category.
- Rollback removes or restores only rows created/updated by that batch.
- Keep a pre-promotion summary of product count, offer count, affected barcodes, and affected retailers.
- Never rollback unrelated user/account/subscription/community data.
- If rollback affects shared product rows, preserve better verified data from earlier sources.

## Data Quality Rules

- Barcodes must be real GTIN/EAN/UPC values with valid checksum.
- Product names must come from approved source data or manual verified entry.
- Ingredients and allergens must be copied only from approved/verified source data.
- Prices and stock must be timestamped and source-specific.
- URLs must come only from approved source data.
- If source quality is unclear, stage as unknown and do not promote until clarified.
- Retailer offers and product safety data must have separate freshness/verification status.

## Unknown-Data Handling

- Missing ingredients: keep blank/unknown and do not infer safety.
- Missing allergens: keep blank/unknown and do not infer allergen absence.
- Missing price: keep null/blank and do not create a price comparison claim.
- Missing stock: use `unknown`.
- Missing URL: keep blank and do not invent a URL.
- Missing image: keep blank and use UI fallback only.
- Missing source URL: allowed for manual CSV/local business only when source records are otherwise documented.

## Duplicate Prevention

- Block duplicate `barcode + retailer` rows inside the same batch.
- Normalise retailer names before duplicate checks.
- Normalise barcode digits before duplicate checks.
- Do not create separate products for the same barcode.
- If a barcode exists, update only fields permitted by source-strength rules.
- If two sources disagree, preserve the strongest verified source and record the conflict for manual review.

## Import Safety Rules

- Importers must not scrape.
- Importers must not guess.
- Importers must skip bad rows without crashing.
- Importers must log blocked rows and reasons.
- Importers must keep safety analysis separate from availability.
- Importers must preserve existing verified fields when incoming data is weaker or missing.
- Importers must support dry-run mode.
- Importers must fail closed: validation errors block promotion.

## Expansion Phases

Phase A: structure and validation

- Create retailer/category CSV structure.
- Keep files header-only unless real approved data exists.
- Run strict validation on all staged CSVs.

Phase B: Baby & Toddler core retailer expansion

- Baby formula, baby meals, baby porridge, fruit puree, baby snacks, toddler yoghurt.
- Start with Tesco, Asda, Sainsbury's, Waitrose, Ocado, Morrisons, and M&S.

Phase C: complete Baby & Toddler core coverage

- Increase batch size to 50 to 100 rows per retailer/category after proof batches pass.
- Add extended retailers only when approved feeds or manual verified data are available.

Phase D: allergy-sensitive food expansion

- Free-from, dairy alternatives, gluten-free, nut-sensitive categories.
- Preserve strict unknown handling for ingredients/allergens.

Phase E: everyday supermarket comparison expansion

- Cereals, snacks, drinks, ready meals, frozen, sauces, pantry.
- Prioritise offer freshness, retailer coverage, and duplicate prevention.

Phase F: SafeHome starter expansion

- Household cleaning, laundry, dishwasher, and surface cleaners.
- Keep SafeHome hazard/safety logic separate from SafeBite food logic.

Phase G: high-volume feed/API scaling

- Use only licensed feeds, approved APIs, supplier feeds, affiliate feeds, manual CSVs, or local business data.
- Promote only after validation, dry-run, and rollback readiness are confirmed.
