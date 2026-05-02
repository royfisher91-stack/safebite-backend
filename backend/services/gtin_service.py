import re
from typing import Tuple

_GTIN_RE = re.compile(r"^\d{8}$|^\d{12}$|^\d{13}$|^\d{14}$")


def normalise_barcode(raw: object) -> str:
    if raw is None:
        return ""
    return re.sub(r"\D", "", str(raw).strip())


def is_valid_gtin_format(barcode: object) -> bool:
    return bool(_GTIN_RE.match(normalise_barcode(barcode)))


def compute_gtin_check_digit(body: str) -> int:
    digits = [int(ch) for ch in body]
    total = 0
    for index, digit in enumerate(reversed(digits), start=1):
        total += digit * 3 if index % 2 == 1 else digit
    return (10 - (total % 10)) % 10


def is_valid_gtin(barcode: object) -> bool:
    value = normalise_barcode(barcode)
    if not is_valid_gtin_format(value):
        return False
    body = value[:-1]
    check_digit = int(value[-1])
    return compute_gtin_check_digit(body) == check_digit


def classify_gtin(barcode: object) -> str:
    value = normalise_barcode(barcode)
    if len(value) == 8:
        return "GTIN-8"
    if len(value) == 12:
        return "GTIN-12/UPC"
    if len(value) == 13:
        return "GTIN-13/EAN-13"
    if len(value) == 14:
        return "GTIN-14"
    return "UNKNOWN"


def validate_gtin(barcode: object) -> Tuple[bool, str]:
    value = normalise_barcode(barcode)
    if not value:
        return False, "barcode missing"
    if not is_valid_gtin_format(value):
        return False, "barcode has invalid GTIN length/format"
    if not is_valid_gtin(value):
        return False, "barcode failed GTIN checksum"
    return True, classify_gtin(value)
