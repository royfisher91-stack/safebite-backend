from typing import Any, Dict, List, Optional


def build_explanation(
    title: str,
    summary: str,
    flags: Optional[List[str]] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "title": str(title or "").strip() or "Safety explanation",
        "summary": str(summary or "").strip(),
        "flags": sorted(set(flags or [])),
        "details": details or {},
    }


def explanation_from_result(result: Dict[str, Any]) -> Dict[str, Any]:
    return build_explanation(
        title=str(result.get("safety_result") or "Unknown"),
        summary=str(result.get("reasoning") or result.get("ingredient_reasoning") or ""),
        flags=result.get("unknown_flags") or [],
        details=result,
    )
