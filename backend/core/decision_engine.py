from typing import Any, Callable, Dict

from core.unknowns import build_unknown_result


AnalysisFunction = Callable[[Dict[str, Any]], Dict[str, Any]]


def run_decision_pipeline(
    module_code: str,
    product: Dict[str, Any],
    analyser: AnalysisFunction,
) -> Dict[str, Any]:
    if not callable(analyser):
        return build_unknown_result(
            "No analyser is registered for module {0}.".format(module_code),
            ["missing_analyser_flag"],
        )

    payload = analyser(product or {})
    if not isinstance(payload, dict):
        return build_unknown_result(
            "Analyser for module {0} returned an invalid payload.".format(module_code),
            ["invalid_analyser_payload_flag"],
        )

    shaped = dict(payload)
    shaped.setdefault("module_code", module_code)
    shaped.setdefault("unknown_flags", [])
    return shaped
