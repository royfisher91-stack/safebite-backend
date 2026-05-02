from typing import Any, Dict

from imports.retailer_adapters.common import map_standard_row


RETAILER = "Ocado"


def adapt_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return map_standard_row(row, RETAILER)

