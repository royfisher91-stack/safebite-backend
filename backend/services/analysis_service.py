from typing import Any, Dict

from domains.food.services.food_analysis import analyse_food_product


def analyse_product(product: Dict[str, Any]) -> Dict[str, Any]:
    return analyse_food_product(product or {})


def build_analysis(product: Dict[str, Any]) -> Dict[str, Any]:
    return analyse_product(product)
