from typing import Any, Dict

from core.alternatives_engine import run_alternatives_pipeline


MODULE_CODE = "safebite_food"


def _build_existing_food_alternatives(product: Dict[str, Any]) -> Dict[str, Any]:
    from services.alternatives_service import build_alternatives

    return build_alternatives(product or {})


def build_food_alternatives(product: Dict[str, Any]) -> Dict[str, Any]:
    return run_alternatives_pipeline(
        MODULE_CODE,
        product or {},
        _build_existing_food_alternatives,
    )
