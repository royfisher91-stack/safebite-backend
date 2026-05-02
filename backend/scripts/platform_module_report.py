from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _missing_files() -> List[str]:
    required = [
        "core/decision_engine.py",
        "core/pricing_engine.py",
        "core/alternatives_engine.py",
        "core/explanation_engine.py",
        "core/unknowns.py",
        "core/registry.py",
        "domains/food/services/food_analysis.py",
        "domains/food/services/food_pricing.py",
        "domains/food/services/food_alternatives.py",
        "domains/home/services/home_analysis.py",
        "domains/home/services/home_pricing.py",
        "domains/home/services/home_alternatives.py",
        "sources/adapters/source_base.py",
    ]
    return [relative for relative in required if not (ROOT / relative).exists()]


def main() -> int:
    from core.registry import list_modules

    modules: List[Dict[str, Any]] = list_modules()
    missing = _missing_files()
    warnings: List[str] = []
    errors: List[str] = []

    if missing:
        errors.extend("Missing file: {0}".format(item) for item in missing)

    print("PHASE 10 PLATFORM MODULE REPORT")
    print("=" * 80)
    print("Registered modules: {0}".format(len(modules)))
    print("")

    for module in modules:
        print("{0} ({1})".format(module.get("display_name"), module.get("module_code")))
        print("- domain: {0}".format(module.get("domain")))
        print("- enabled_features: {0}".format(", ".join(module.get("enabled_features") or [])))
        print("- source_pack: {0}".format(module.get("source_pack")))
        print("- rule_pack: {0}".format(module.get("rule_pack")))
        print("- subscription_requirement: {0}".format(module.get("requires_subscription")))
        print("")

    print("Missing files")
    if missing:
        for item in missing:
            print("- {0}".format(item))
    else:
        print("- none")

    print("")
    print("Warning count: {0}".format(len(warnings)))
    print("Error count: {0}".format(len(errors)))
    for warning in warnings:
        print("[WARN] {0}".format(warning))
    for error in errors:
        print("[ERROR] {0}".format(error))

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
