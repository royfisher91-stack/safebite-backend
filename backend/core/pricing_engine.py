from typing import Any, Callable, Dict, List


PricingFunction = Callable[[List[Dict[str, Any]]], Dict[str, Any]]


def run_pricing_pipeline(
    module_code: str,
    offers: List[Dict[str, Any]],
    pricing_builder: PricingFunction,
) -> Dict[str, Any]:
    if not callable(pricing_builder):
        return {
            "module_code": module_code,
            "best_price": None,
            "pricing_summary": "No pricing builder is registered.",
            "unknown_flags": ["missing_pricing_builder_flag"],
        }

    payload = pricing_builder(offers or [])
    if not isinstance(payload, dict):
        return {
            "module_code": module_code,
            "best_price": None,
            "pricing_summary": "Pricing builder returned an invalid payload.",
            "unknown_flags": ["invalid_pricing_payload_flag"],
        }

    shaped = dict(payload)
    shaped.setdefault("module_code", module_code)
    shaped.setdefault("unknown_flags", [])
    return shaped
