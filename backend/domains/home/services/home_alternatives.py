from typing import Any, Dict

from core.alternatives_engine import EMPTY_ALTERNATIVES, run_alternatives_pipeline


MODULE_CODE = "safehome"


def _build_home_alternatives(product: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(EMPTY_ALTERNATIVES)
    payload["unknown_flags"] = ["safehome_alternatives_unavailable_flag"]
    payload["summary"] = "SafeHome alternatives need verified household product data before recommendations are enabled."
    return payload


def build_home_alternatives(product: Dict[str, Any]) -> Dict[str, Any]:
    return run_alternatives_pipeline(MODULE_CODE, product or {}, _build_home_alternatives)
