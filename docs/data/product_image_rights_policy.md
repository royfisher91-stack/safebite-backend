# SafeBite Product Image Rights Policy

TODO: solicitor review before public launch.

SafeBite can show product pictures only when the image rights are clear. A product `image_url` alone is not enough for public display.

## Allowed Image Sources

- SafeBite placeholder images.
- SafeBite-owned verified product or packaging photos.
- Manufacturer images where permission is granted or licence terms allow use.
- Retailer/product images only where permission, approved API terms, affiliate feed terms, or a written licence allows use.
- Licensed product-feed images.

## Blocked Image Sources

- Retailer or manufacturer stock photos copied from websites when rights are unknown.
- Product images hosted only because they appear publicly online.
- Scraped images without permission.

## Required Product Image Fields

- `image_url`
- `image_source_type`
- `image_rights_status`
- `image_credit`
- `image_last_verified_at`

Allowed `image_source_type` values:

- `safebite_placeholder`
- `own_packaging_photo`
- `manufacturer_image`
- `retailer_image`
- `licensed_feed_image`

Allowed `image_rights_status` values:

- `not_required`
- `permission_granted`
- `licensed`
- `approved_feed_terms`
- `unknown_blocked`

## Public App Rule

If `image_rights_status` is `unknown_blocked`, SafeBite must show its placeholder instead of the product image. Manufacturer images should be labelled internally as `Manufacturer image`. If a licence requires public credit, the required credit must be stored in `image_credit` and displayed beside the product image.

## Import Rule

Controlled CSV/API/feed imports may include product image URLs only with the required provenance fields. If an import row contains `image_url` without clear rights metadata, SafeBite stores the image metadata as `unknown_blocked` and the public app shows the placeholder.
