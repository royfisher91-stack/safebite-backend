# SafeBite Data Safety Draft

TODO: Google Play Data Safety and App Store privacy answers must be reviewed before submission.
TODO: This draft does not claim final legal approval.

## App Name

SafeBite

## Data Types Collected Draft

### Account Information

- Account email
- User ID
- Authentication/session state

Purpose: account creation, login, account-linked data, security, subscription access.

### App Activity

- Saved products
- Favourites
- Scan/search history if enabled
- Product lookup activity such as barcode or search text

Purpose: product checking, history, favourites, saved items, and user convenience.

### Subscription Data

- Subscription status
- Plan code
- Entitlement state
- Provider/platform
- Product ID
- Purchase token or transaction ID reference where needed for verification
- Expiry/cancellation state

Purpose: billing verification, subscription access, restore purchases, support, entitlement checks.

### Optional Health/Profile-Related Preferences

- Optional allergy/profile information if enabled
- Optional condition or preference fields if enabled

Purpose: personalising product checks and warnings.

TODO: Legal review required for health/allergy profile classification and store disclosure wording.

### Support Data

- Contact email
- Support messages
- Barcode/product details submitted by the user
- Screenshots if the user chooses to provide them

Purpose: support, bug fixing, product data correction, account help.

## Data Shared Draft

TODO: Confirm final processor/vendor list.

Potential sharing categories:

- App Store / Google Play billing for purchase and subscription handling
- Hosting/database providers needed to run SafeBite
- Authentication/session infrastructure
- Customer support tools if added
- Analytics/crash reporting if added

Do not mark analytics/crash reporting as used unless it is actually added before submission.

## Encryption / Transport

TODO: Confirm production hosting and transport security before submission.

Draft expectation: production API traffic should use HTTPS. Passwords should not be stored in plain text.

## Data Deletion

Users can request deletion through the Data Deletion Request page or by contacting the privacy/support address.

TODO: Add final deletion URL.

Draft deletion process:

1. User requests deletion.
2. SafeBite verifies account ownership if needed.
3. SafeBite deletes or anonymises account-linked saved products, favourites, scan/search history, and profile data where no longer required.
4. Subscription/payment records may remain with App Store, Google Play, or another payment provider as required by platform, billing, tax, dispute, or refund processes.

## Product Safety Disclaimer

SafeBite supports product checking and comparison, but does not replace medical, allergy, nutrition, emergency, manufacturer, or professional advice.

## Supermarket Price/Stock Disclaimer

Retailer prices, promotions, stock status, and availability can change and may be incomplete or out of date.

## SafeHome Add-on Disclaimer

SafeHome is a planned paid add-on via `safehome_addon`. It does not replace manufacturer instructions, hazard labels, emergency guidance, or professional safety advice.
