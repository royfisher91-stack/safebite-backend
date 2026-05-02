from typing import Any, Callable, Dict


AlternativesFunction = Callable[[Dict[str, Any]], Dict[str, Any]]


EMPTY_ALTERNATIVES = {
    "safer_option": None,
    "cheaper_option": None,
    "same_category_option": None,
}


def run_alternatives_pipeline(
    module_code: str,
    product: Dict[str, Any],
    alternatives_builder: AlternativesFunction,
) -> Dict[str, Any]:
    if not callable(alternatives_builder):
        payload = dict(EMPTY_ALTERNATIVES)
        payload["module_code"] = module_code
        payload["unknown_flags"] = ["missing_alternatives_builder_flag"]
        return payload

    payload = alternatives_builder(product or {})
    if not isinstance(payload, dict):
        shaped = dict(EMPTY_ALTERNATIVES)
        shaped["module_code"] = module_code
        shaped["unknown_flags"] = ["invalid_alternatives_payload_flag"]
        return shaped

    shaped = dict(EMPTY_ALTERNATIVES)
    shaped.update(payload)
    shaped.setdefault("module_code", module_code)
    shaped.setdefault("unknown_flags", [])
    return shaped
