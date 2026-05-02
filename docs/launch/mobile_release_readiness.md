# SafeBite Mobile Release Readiness

Status: pre-release ready for internal testing, not ready to publish until the TODOs below are closed.

## App Identity

- App name is configured as `SafeBite` in `mobile-app/app.json`.
- Expo slug is `safebite-mobile`.
- iOS bundle identifier is currently `com.safebite.mobile`.
- Android package is currently `com.safebite.mobile`.
- TODO: Confirm final bundle/package ownership before App Store Connect and Google Play Console submission.

## Store Visual Assets

- Placeholder app icon wiring is present:
  - `mobile-app/assets/icon.png`
  - `mobile-app/assets/adaptive-icon.png`
- Placeholder splash screen wiring is present:
  - `mobile-app/assets/splash.png`
  - splash background `#EEF8F5`
- TODO: Replace placeholders with final square App Store and Google Play production artwork.
- TODO: Check iOS icon safe area, Android adaptive icon mask, and splash rendering on real devices.

## Account And Settings Links

The account screen includes links for:

- Privacy Policy
- Terms of Use
- Subscription Terms
- Data Deletion Request
- Contact / Support

The account screen also includes:

- Manage Subscription
- Restore Purchases
- SafeHome Add-on
- Logout

TODO: Replace `safebite.example` placeholder URLs with final production URLs before submission.

## Subscription And Billing

- SafeBite Core displays the locked launch price of `GBP 5/month`.
- Billing screens are placeholders only and do not create fake payment success.
- Paid access remains dependent on backend provider verification.
- Manage and restore copy explains App Store / Google Play subscription management.
- TODO: Connect RevenueCat or store billing SDK before production billing.
- TODO: Complete sandbox purchase, restore, cancellation, expiry, and refund testing.

## SafeHome Add-On Gate

- SafeHome is shown as a paid add-on using `safehome_addon`.
- The billing screen now shows SafeHome as locked until a verified add-on entitlement is present.
- SafeHome copy states it does not change SafeBite food safety scoring.
- TODO: Re-test once live RevenueCat add-on entitlements are wired through mobile.

## Scanner And Manual Barcode Fallback

- Scanner uses `expo-camera`.
- Camera permission copy is configured.
- Manual barcode fallback is present on the scanner screen.
- Search screen also supports direct barcode opening.
- TODO: Test permission denied, permission allowed, bad barcode, and known barcode flows on iOS and Android devices.

## Backend Offline And Error States

- API client now catches network failures and returns a user-readable backend offline message.
- Product, alternatives, account, billing, health, saved, and profile flows already catch API errors and show controlled alerts or empty states.
- TODO: Test against no network, backend stopped, backend 401, backend 404, and backend 500 scenarios.

## Unknown Or Missing Data

- Product and alternatives types allow optional/unknown fields.
- UI surfaces use unknown, unavailable, or empty states instead of guessing missing data.
- SafeBite must not produce a definitive safety result when ingredient/allergen data is absent.
- TODO: Add a manual QA case using a product with missing ingredients/allergens before release approval.

## Dark Mode

- Expo `userInterfaceStyle` is set to `automatic`.
- The app theme includes light and dark palettes.
- TODO: Manually verify text contrast on Home, Search, Scanner, Health, Saved, Account, Billing, Product Detail, and Alternatives screens.

## Crash Checks

- TODO: Test cold launch, background/foreground, register, login, logout, scanner, product lookup, saved items, billing screens, support/legal links, and unknown product handling on iOS and Android.

## Validation Run

Run from `mobile-app`:

```bash
npm run typecheck
npx expo config --type public
```

Current validation result:

- `npm run typecheck`: PASS on 2026-04-29.
- `npx expo config --type public`: PASS on 2026-04-29.
- Expo config confirms app name `SafeBite`, iOS bundle identifier `com.safebite.mobile`, Android package `com.safebite.mobile`, icon wiring, splash wiring, camera permission copy, and Android blocked permission for `android.permission.RECORD_AUDIO`.

## Publish Blockers

- TODO: Replace placeholder icon/splash art with final production assets.
- TODO: Replace placeholder legal/support URLs with final URLs.
- TODO: Confirm final iOS bundle identifier and Android package.
- TODO: Configure live RevenueCat/App Store/Google Play billing.
- TODO: Complete store sandbox purchase and restore testing.
- TODO: Complete physical-device camera and dark-mode QA.

Final note: do not publish until all TODOs above are resolved or explicitly accepted for a test-only release.
