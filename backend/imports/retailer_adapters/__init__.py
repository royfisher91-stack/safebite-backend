from typing import Any, Dict

from imports.retailer_adapters.common import map_standard_row


def adapt_row(row: Dict[str, Any], retailer: str) -> Dict[str, Any]:
    return map_standard_row(row, retailer)

