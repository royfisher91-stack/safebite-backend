from typing import Any, Dict, List

from core.pricing_engine import run_pricing_pipeline


MODULE_CODE = "safehome"


def _build_home_pricing_summary(offers: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "best_price": None,
        "lowest_price": None,
        "cheapest_retailer": None,
        "offer_count": len(offers or []),
        "pricing_summary": "SafeHome pricing is not connected to household retailer data yet.",
        "unknown_flags": ["safehome_pricing_unavailable_flag"],
    }


def build_home_pricing_summary(offers: List[Dict[str, Any]]) -> Dict[str, Any]:
    return run_pricing_pipeline(MODULE_CODE, offers or [], _build_home_pricing_summary)
