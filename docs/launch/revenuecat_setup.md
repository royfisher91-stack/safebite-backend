# SafeBite RevenueCat Setup Draft

TODO: Final RevenueCat, App Store Connect, and Google Play Console setup must be checked before production billing is enabled.
TODO: Do not commit real RevenueCat, Apple, Google, or Stripe secret keys.

## Goal

Prepare SafeBite billing for RevenueCat without requiring live Apple or Google production setup yet.

SafeBite billing must keep the locked security rule:

- Never grant paid access unless provider verification succeeds.
- Promo/influencer access may still grant access through the existing promo flow.

## Product IDs

Use these product IDs consistently across SafeBite, RevenueCat, App Store Connect, and Google Play Console:

- SafeBite Core monthly subscription: `safebite_core_monthly`
- SafeHome paid add-on: `safehome_addon`

## Environment Placeholders

Add these values through the deployment environment or local `.env` tooling. Do not commit real values.

```text
REVENUECAT_PROJECT_ID=TODO
REVENUECAT_API_KEY=TODO
REVENUECAT_WEBHOOK_SECRET=TODO
REVENUECAT_ENV=development
APPLE_PRODUCT_ID=safebite_core_monthly
GOOGLE_PRODUCT_ID=safebite_core_monthly
SAFEHOME_ADDON_PRODUCT_ID=safehome_addon
```

Use `REVENUECAT_ENV=development` until sandbox and test-store flows pass. Switch to `production` only after review.

## Step 1: Create RevenueCat Account

1. Create or open the RevenueCat account for SafeBite.
2. Create a SafeBite project.
3. Record the project ID in the deployment environment as `REVENUECAT_PROJECT_ID`.
4. Create API keys only in RevenueCat.
5. Store keys in the deployment secret manager as `REVENUECAT_API_KEY`.

## Step 2: Use RevenueCat Test Store First

If App Store Connect or Google Play Console products are not ready, use RevenueCat Test Store first.

Create Test Store products:

- `safebite_core_monthly`
- `safehome_addon`

Use Test Store purchases to check app UI, entitlement mapping, restore purchases, and webhook handling before live store products exist.

## Step 3: Create App Store Connect Products Later

When Apple setup is ready:

1. Create the SafeBite app in App Store Connect.
2. Create the subscription product matching `safebite_core_monthly`.
3. Create the SafeHome add-on product matching `safehome_addon` if it will be sold through Apple.
4. Configure sandbox testers.
5. Import or link the products into RevenueCat.
6. Test sandbox purchase, restore, expiry, cancellation, and refund states.

TODO: Confirm final Apple subscription group and product type for SafeHome.

## Step 4: Create Google Play Products Later

When Google Play setup is ready:

1. Create the SafeBite app in Google Play Console.
2. Create the subscription/base plan matching `safebite_core_monthly`.
3. Create the SafeHome add-on product matching `safehome_addon` if it will be sold through Google Play.
4. Configure licence testers.
5. Import or link the products into RevenueCat.
6. Test sandbox purchase, restore, expiry, cancellation, and refund states.

TODO: Confirm final Google Play base plan and offer IDs.

## Step 5: Configure RevenueCat Entitlements

Create RevenueCat entitlements that map to SafeBite access:

- `safebite_core`: maps to `safebite_core_monthly`
- `safehome_addon`: maps to `safehome_addon`

SafeBite backend must only mark paid access active after RevenueCat/provider verification confirms the subscription or add-on is active.

## Step 6: Webhook Setup

Configure the RevenueCat webhook URL after backend hosting is final.

TODO: Add final webhook URL.

Store webhook secret as:

```text
REVENUECAT_WEBHOOK_SECRET=TODO
```

Webhook handling should verify the webhook secret before updating subscription status.

## Step 7: Do Not Enable Production Billing Early

Do not enable production billing until all of these pass:

- RevenueCat Test Store purchase and restore tests.
- Apple sandbox purchase and restore tests, if iOS is live.
- Google Play test purchase and restore tests, if Android is live.
- Backend `/billing/verify` does not grant access for unverified purchases.
- Promo/influencer access still works.
- SafeHome add-on requires `safehome_addon` entitlement.

## Current SafeBite Backend Routes

- `GET /billing/products`
- `POST /billing/verify`
- `GET /subscription/entitlement`
- `GET /subscription/status`
- `GET /entitlement`

## Current Mobile Billing Screens

- Subscribe
- Manage Subscription
- Restore Purchases
- SafeHome Add-on

These are billing-ready placeholders and must not show fake payment success.
