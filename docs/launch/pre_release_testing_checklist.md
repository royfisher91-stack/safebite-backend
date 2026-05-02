# SafeBite Pre-Release Testing Checklist

TODO: Complete this checklist before each App Store, Google Play, or public web release. This is a product QA checklist, not legal, medical, allergy, nutrition, or professional advice.

## Release Build Details

- Release version: TODO
- Build number: TODO
- Backend environment: TODO
- Mobile platform(s): TODO
- Tester: TODO
- Date: TODO
- Known backend validation result: TODO

## Account Registration

- Create a new account with a valid email and strong password.
- Confirm duplicate registration is handled cleanly.
- Confirm weak or malformed credentials are rejected.
- Confirm account-specific data is not visible before login.
- Confirm registration errors are readable on mobile and web.

## Login And Logout

- Log in with the newly created account.
- Confirm invalid credentials are rejected.
- Confirm logout removes local session state.
- Confirm protected account screens require login after logout.
- Confirm token expiry or bad token handling shows a safe sign-in path.

## Subscription Entitlement

- Confirm free entitlement state is shown before purchase.
- Confirm paid entitlement is not granted without verified App Store, Google Play, RevenueCat, or approved provider verification.
- Confirm subscription status text matches the active plan state.
- Confirm cancellation wording explains that subscriptions are managed through App Store or Google Play where applicable.
- Confirm SafeBite core pricing displays as GBP5/month.

## Promo And Influencer Access

- Apply a valid promo or influencer code in a test account.
- Confirm entitlement is granted only for the intended account.
- Confirm invalid, expired, or empty promo codes are rejected.
- Confirm promo access still preserves the normal paid billing security rule.

## Product Barcode Lookup

- Scan or manually enter known barcode `5056000505910`.
- Confirm the product page loads.
- Confirm product name, brand, category, ingredients, allergens, and data quality status render without layout breakage.
- Confirm unknown barcode handling is clear and does not crash.

## Offers Lookup

- Open offers for known barcode `5056000505910`.
- Confirm retailers, prices, promo prices, multibuy text, and stock status display only where known.
- Confirm missing prices, unknown stock, and missing URLs render as unknown or unavailable, not guessed.

## Alternatives Lookup

- Open alternatives for known barcode `5056000505910`.
- Confirm alternatives are listed when available.
- Confirm empty alternatives state is clear.
- Confirm cheaper or safer labels only appear when backed by existing verified data.

## Retailer Stockists

- Open stockists for known barcode `5056000505910`.
- Confirm stockists show retailer names and known stock status.
- Confirm unknown stock is labelled unknown.
- Confirm the screen does not imply availability where no retailer offer exists.

## Supermarket Coverage

- Confirm current active supermarket coverage focuses on Tesco, Asda, Sainsbury's, Waitrose, Ocado, and Iceland.
- Confirm later-stage retailers do not cause warnings, failures, or thin-coverage blocking.
- Confirm retailer coverage is separate from product safety analysis.
- Confirm future-compatible retailers can be listed as future only where the architecture already supports them.

## SafeHome Add-On Access Gate

- Confirm SafeHome is visible as a paid add-on or gated module.
- Confirm users without SafeHome entitlement cannot access paid SafeHome features.
- Confirm users with valid SafeHome entitlement can access the intended starter/add-on experience.
- Confirm SafeHome does not alter SafeBite food product safety scoring.

## Privacy, Terms, And Support Links

- Open Privacy Policy, Terms of Use, Subscription Terms, Data Deletion Request, Contact, and Support links.
- Confirm each link opens the expected page or screen.
- Confirm placeholder legal pages include TODO markers for solicitor/legal review.
- Confirm support/contact email placeholders are clear and not presented as final if not final.

## Mobile Scanner And Manual Barcode Fallback

- Confirm camera scanner opens on supported devices.
- Deny camera permission and confirm the app offers manual barcode entry.
- Enter known barcode `5056000505910` manually.
- Enter an invalid barcode and confirm safe error handling.
- Confirm scanner failure does not crash the app.

## Dark Mode Text Visibility

- Test account, product, offers, alternatives, billing, support, and legal screens in dark mode.
- Confirm text contrast is readable.
- Confirm disabled states, links, form placeholders, and error messages remain visible.
- Confirm no white-on-white or dark-on-dark text appears.

## Broken Links

- Tap every footer, account, settings, legal, support, pricing, app download placeholder, and SafeHome link.
- Confirm external placeholder links are labelled TODO if not final.
- Confirm app download placeholder buttons do not imply live store availability before launch.
- Confirm broken routes show a controlled error or safe fallback.

## App Crash Checks

- Cold launch the app.
- Background and foreground the app.
- Log in, log out, and repeat.
- Open product lookup, scanner, account, billing, support, and legal screens.
- Confirm no visible crashes, native red screens, unhandled promise errors, or blank screens.

## Empty And Unknown Data Handling

- Test products or offers with missing price, stock, image, URL, ingredients, or allergens.
- Confirm missing data is shown as unknown, unavailable, or not provided.
- Confirm the app does not invent values or hide uncertainty.
- Confirm layout remains stable when data fields are empty.

## No Guessed Safety Result For Missing Ingredients Or Allergens

- Test a product with missing ingredients and allergens.
- Confirm SafeBite does not produce a guessed definitive safety result.
- Confirm the UI explains that safety analysis is limited when ingredient or allergen data is missing.
- Confirm retailer availability never upgrades or downgrades product safety scoring.

## Backend Smoke Test

From `/Users/royfisher/Desktop/product-safety-app/backend`, run:

```bash
./.venv/bin/python scripts/pre_release_smoke_test.py
./.venv/bin/python validate_backend.py
./.venv/bin/python coverage_summary_report.py
./.venv/bin/python alternatives_quality_report.py
```

Expected:

- Smoke test: PASS
- Backend validation warnings: 0
- Backend validation errors: 0
- Coverage report issue_count: 0
- Alternatives report issue_count: 0

## Release Decision

- Manual checklist result: TODO PASS/FAIL
- Automated smoke test result: TODO PASS/FAIL
- Backend validation result: TODO PASS/FAIL
- Known issues accepted for release: TODO
- Final release decision: TODO
