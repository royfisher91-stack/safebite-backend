from typing import Any, Dict, List, Optional


def build_unknown_result(
    reason: str,
    flags: Optional[List[str]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "safety_result": "Unknown",
        "safety_score": None,
        "reasoning": reason,
        "unknown_flags": sorted(set(flags or ["data_unavailable_flag"])),
    }
    if extra:
        payload.update(extra)
    return payload


def merge_unknown_flags(*groups: Optional[List[str]]) -> List[str]:
    flags = []
    seen = set()
    for group in groups:
        for flag in group or []:
            cleaned = str(flag or "").strip()
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            flags.append(cleaned)
    return flags
