from typing import Any, Dict


ALLOWED_IMAGE_SOURCE_TYPES = {
    "safebite_placeholder",
    "own_packaging_photo",
    "manufacturer_image",
    "retailer_image",
    "licensed_feed_image",
}

ALLOWED_IMAGE_RIGHTS_STATUSES = {
    "not_required",
    "permission_granted",
    "licensed",
    "approved_feed_terms",
    "unknown_blocked",
}

IMAGE_SOURCE_LABELS = {
    "safebite_placeholder": "SafeBite placeholder",
    "own_packaging_photo": "SafeBite packaging photo",
    "manufacturer_image": "Manufacturer image",
    "retailer_image": "Retailer/feed image",
    "licensed_feed_image": "Licensed feed image",
}

_EXTERNAL_IMAGE_SOURCES = {
    "manufacturer_image",
    "retailer_image",
    "licensed_feed_image",
}

_PUBLIC_RIGHTS_BY_SOURCE = {
    "own_packaging_photo": {"not_required", "permission_granted", "licensed"},
    "manufacturer_image": {"permission_granted", "licensed", "approved_feed_terms"},
    "retailer_image": {"permission_granted", "licensed", "approved_feed_terms"},
    "licensed_feed_image": {"licensed", "approved_feed_terms", "permission_granted"},
}


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalise_token(value: Any) -> str:
    return _clean(value).lower().replace(" ", "_").replace("-", "_")


def normalise_image_source_type(value: Any, image_url: Any = "") -> str:
    token = _normalise_token(value)
    if token in ALLOWED_IMAGE_SOURCE_TYPES:
        return token
    if not _clean(image_url):
        return "safebite_placeholder"
    return "safebite_placeholder"


def normalise_image_rights_status(value: Any, image_url: Any = "", source_type: Any = "") -> str:
    token = _normalise_token(value)
    image_url_text = _clean(image_url)
    source = normalise_image_source_type(source_type, image_url_text)

    if not image_url_text:
        return "not_required"
    if token not in ALLOWED_IMAGE_RIGHTS_STATUSES:
        return "unknown_blocked"
    if token == "unknown_blocked":
        return token
    if source in _EXTERNAL_IMAGE_SOURCES and token == "not_required":
        return "unknown_blocked"
    return token


def normalise_image_metadata(payload: Dict[str, Any]) -> Dict[str, str]:
    image_url = _clean(payload.get("image_url"))
    source_present = bool(_clean(payload.get("image_source_type")))
    rights_present = bool(_clean(payload.get("image_rights_status")))

    source_type = normalise_image_source_type(payload.get("image_source_type"), image_url)
    rights_status = normalise_image_rights_status(payload.get("image_rights_status"), image_url, source_type)

    if image_url and (not source_present or not rights_present):
        rights_status = "unknown_blocked"

    return {
        "image_source_type": source_type,
        "image_rights_status": rights_status,
        "image_credit": _clean(payload.get("image_credit")),
        "image_last_verified_at": _clean(payload.get("image_last_verified_at")),
    }


def is_public_image_allowed(image_url: Any, source_type: Any, rights_status: Any) -> bool:
    if not _clean(image_url):
        return False

    source = normalise_image_source_type(source_type, image_url)
    rights = normalise_image_rights_status(rights_status, image_url, source)
    if rights == "unknown_blocked":
        return False

    return rights in _PUBLIC_RIGHTS_BY_SOURCE.get(source, set())


def public_image_url(image_url: Any, source_type: Any, rights_status: Any) -> str:
    return _clean(image_url) if is_public_image_allowed(image_url, source_type, rights_status) else ""


def image_source_label(source_type: Any) -> str:
    source = normalise_image_source_type(source_type)
    return IMAGE_SOURCE_LABELS.get(source, "SafeBite placeholder")
