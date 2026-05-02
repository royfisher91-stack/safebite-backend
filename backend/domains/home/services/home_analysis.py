from typing import Any, Dict, List

from core.unknowns import build_unknown_result


MODULE_CODE = "safehome"


def analyse_home_product(product: Dict[str, Any]) -> Dict[str, Any]:
    hazard_data = product.get("hazard_data") or product.get("chemical_hazards")
    if not hazard_data:
        return build_unknown_result(
            "SafeHome hazard data is not available for this household product yet.",
            ["missing_hazard_data_flag", "safehome_data_unavailable_flag"],
            {
                "module_code": MODULE_CODE,
                "child_safety_flags": [],
                "irritation_flags": [],
                "inhalation_flags": [],
                "environmental_flags": [],
            },
        )

    flags: List[str] = []
    text = " ".join(str(item).lower() for item in hazard_data if str(item).strip())
    if "child" in text or "keep out of reach" in text:
        flags.append("child_safety_flag")
    if "irritant" in text or "skin" in text:
        flags.append("skin_irritation_flag")
    if "inhalation" in text or "spray" in text:
        flags.append("inhalation_flag")

    result = "Caution" if flags else "Unknown"
    score = 50 if flags else None
    return {
        "module_code": MODULE_CODE,
        "safety_result": result,
        "safety_score": score,
        "reasoning": "SafeHome starter analysis uses explicit household hazard data only.",
        "child_safety_flags": [flag for flag in flags if flag == "child_safety_flag"],
        "irritation_flags": [flag for flag in flags if flag == "skin_irritation_flag"],
        "inhalation_flags": [flag for flag in flags if flag == "inhalation_flag"],
        "environmental_flags": [],
        "unknown_flags": [] if flags else ["limited_hazard_data_flag"],
    }
