from typing import Any, Dict

from core.decision_engine import run_decision_pipeline
from services.decision_engine import build_decision


MODULE_CODE = "safebite_food"


def analyse_food_product(product: Dict[str, Any]) -> Dict[str, Any]:
    return run_decision_pipeline(MODULE_CODE, product or {}, build_decision)


def build_food_analysis(product: Dict[str, Any]) -> Dict[str, Any]:
    return analyse_food_product(product)
