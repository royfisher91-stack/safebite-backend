from typing import Any, Dict, List


MODULES: Dict[str, Dict[str, Any]] = {
    "safebite_food": {
        "module_code": "safebite_food",
        "display_name": "SafeBite Food",
        "domain": "food",
        "enabled_features": [
            "ingredient_analysis",
            "allergy_analysis",
            "condition_engine",
            "pricing",
            "alternatives",
            "community_layer",
            "vouchers",
        ],
        "source_pack": "uk_food_retailers",
        "rule_pack": "food_rules_v1",
        "requires_subscription": "base_subscription",
    },
    "safehome": {
        "module_code": "safehome",
        "display_name": "SafeHome",
        "domain": "home",
        "enabled_features": [
            "chemical_analysis",
            "child_safety",
            "pricing",
            "alternatives",
        ],
        "source_pack": "uk_household_retailers",
        "rule_pack": "home_rules_v1",
        "requires_subscription": "safehome_addon",
    },
}


def list_modules() -> List[Dict[str, Any]]:
    return [dict(MODULES[key]) for key in sorted(MODULES.keys())]


def get_module_config(module_code: str) -> Dict[str, Any]:
    cleaned = str(module_code or "").strip().lower()
    config = MODULES.get(cleaned)
    if not config:
        raise ValueError("Unknown module: {0}".format(module_code))
    return dict(config)


def validate_module(module_code: str) -> bool:
    get_module_config(module_code)
    return True


def get_enabled_features(module_code: str) -> List[str]:
    return list(get_module_config(module_code).get("enabled_features", []))


def get_rule_pack(module_code: str) -> str:
    return str(get_module_config(module_code).get("rule_pack") or "")


def get_source_pack(module_code: str) -> str:
    return str(get_module_config(module_code).get("source_pack") or "")


def get_subscription_requirement(module_code: str) -> str:
    return str(get_module_config(module_code).get("requires_subscription") or "")
