from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import List


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


REQUIRED_IMPORTS = [
    "core.decision_engine",
    "core.pricing_engine",
    "core.alternatives_engine",
    "core.explanation_engine",
    "core.unknowns",
    "core.registry",
    "domains.food.services.food_analysis",
    "domains.food.services.food_pricing",
    "domains.food.services.food_alternatives",
    "domains.home.services.home_analysis",
    "domains.home.services.home_pricing",
    "domains.home.services.home_alternatives",
    "domains.home.services.home_sources",
    "sources.adapters.source_base",
    "sources.adapters.tesco_adapter",
    "sources.adapters.asda_adapter",
    "sources.adapters.sainsburys_adapter",
    "services.analysis_service",
    "services.pricing_service",
    "services.alternatives_service",
]


def _file_contains(path: Path, needle: str) -> bool:
    if not path.exists():
        return False
    return needle in path.read_text(encoding="utf-8", errors="ignore").lower()


def main() -> int:
    errors: List[str] = []
    warnings: List[str] = []

    for module_name in REQUIRED_IMPORTS:
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            errors.append("{0} failed to import: {1}".format(module_name, exc))

    from core.registry import get_enabled_features, get_module_config, list_modules, validate_module

    modules = {item["module_code"]: item for item in list_modules()}
    for module_code in ["safebite_food", "safehome"]:
        if module_code not in modules:
            errors.append("{0} is not registered".format(module_code))
        else:
            validate_module(module_code)
            get_module_config(module_code)
            if not get_enabled_features(module_code):
                errors.append("{0} has no enabled features".format(module_code))

    try:
        validate_module("safetech")
        errors.append("Invalid module safetech should not validate")
    except ValueError:
        pass

    food_root = ROOT / "domains" / "food"
    home_root = ROOT / "domains" / "home"
    for path in food_root.rglob("*.py"):
        if _file_contains(path, "domains.home") or _file_contains(path, "safehome"):
            errors.append("Food module depends on home module: {0}".format(path.relative_to(ROOT)))
    for path in home_root.rglob("*.py"):
        if _file_contains(path, "services.decision_engine") or _file_contains(path, "ingredient_engine"):
            errors.append("Home module depends on food scoring: {0}".format(path.relative_to(ROOT)))

    banned_modules = ["safetech", "safecar", "safefinance", "safeproperty"]
    for path in [ROOT / "core" / "registry.py"]:
        for banned in banned_modules:
            if _file_contains(path, banned):
                errors.append("Banned module appears in registry: {0}".format(banned))

    required_files = [
        "domains/home/rules/hazard_rules.json",
        "domains/home/rules/child_safety_rules.json",
        "domains/home/rules/chemical_risk_rules.json",
        "domains/food/rules/ingredient_rules.json",
        "domains/food/rules/allergy_rules.json",
        "domains/food/rules/condition_rules.json",
    ]
    for relative in required_files:
        if not (ROOT / relative).exists():
            errors.append("Missing required file: {0}".format(relative))

    print("Platform core validation")
    print("- warnings: {0}".format(len(warnings)))
    print("- errors: {0}".format(len(errors)))
    for warning in warnings:
        print("[WARN] {0}".format(warning))
    for error in errors:
        print("[ERROR] {0}".format(error))

    if errors:
        return 1

    print("Platform core validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
