import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RESULT_ORDER = {"safe": 1, "caution": 2, "avoid": 3, "unknown": 0}
RESULT_LABEL = {
    "safe": "Safe",
    "caution": "Caution",
    "avoid": "Avoid",
    "unknown": "Unknown",
}
AMBIGUOUS_CATEGORIES = {"flavouring", "other", "herb", "spice"}


def _safe_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    text = str(value).strip()
    return [text] if text else []


def _split_values(values: List[str]) -> List[str]:
    pieces: List[str] = []
    for value in values:
        for piece in str(value or "").split(','):
            trimmed = piece.strip()
            if trimmed:
                pieces.append(trimmed)
    return pieces


def _lower(value: Any) -> str:
    return str(value or "").strip().lower()


def _dedupe_strings(values: List[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        if text not in seen:
            seen.add(text)
            ordered.append(text)
    return ordered


@lru_cache(maxsize=1)
def _load_condition_config() -> Dict[str, Any]:
    path = DATA_DIR / 'condition_rules.json'
    if not path.exists():
        return {"aliases": {}, "conditions": {}}
    return json.loads(path.read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def _load_rule_sets() -> Dict[str, List[Dict[str, Any]]]:
    rule_files = [
        'allergen_rules.json',
        'ibs_rules.json',
        'stoma_rules.json',
        'coeliac_rules.json',
        'baby_sensitivity_rules.json',
    ]
    combined: Dict[str, List[Dict[str, Any]]] = {}
    for filename in rule_files:
        path = DATA_DIR / filename
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding='utf-8'))
        for rule in payload.get('rules', []):
            condition = _lower(rule.get('condition'))
            if not condition:
                continue
            combined.setdefault(condition, []).append(rule)
    return combined


def _supported_conditions(kind: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    conditions = _load_condition_config().get('conditions', {})
    if kind is None:
        return dict(conditions)
    return {
        key: value
        for key, value in conditions.items()
        if _lower(value.get('kind')) == _lower(kind)
    }


def normalise_requested_allergies(values: Optional[List[str]] = None) -> List[str]:
    aliases = {
        _lower(key): _lower(value)
        for key, value in _load_condition_config().get('aliases', {}).items()
    }
    supported = set(_supported_conditions('allergy').keys())
    results: List[str] = []
    for raw in _split_values(_safe_list(values)):
        canonical = aliases.get(_lower(raw), _lower(raw))
        if canonical in supported and canonical not in results:
            results.append(canonical)
    return results


def normalise_requested_conditions(values: Optional[List[str]] = None) -> List[str]:
    aliases = {
        _lower(key): _lower(value)
        for key, value in _load_condition_config().get('aliases', {}).items()
    }
    supported = set(_supported_conditions('condition').keys())
    results: List[str] = []
    for raw in _split_values(_safe_list(values)):
        canonical = aliases.get(_lower(raw), _lower(raw))
        if canonical in supported and canonical not in results:
            results.append(canonical)
    return results


def _collect_ingredient_items(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    ingredient_analysis = analysis.get('ingredient_analysis', {}) or {}
    items = ingredient_analysis.get('items', []) or []
    return [item for item in items if isinstance(item, dict)]


def _collect_allergen_labels(product: Optional[Dict[str, Any]], analysis: Dict[str, Any]) -> List[str]:
    labels = []
    labels.extend(_safe_list((product or {}).get('allergens')))
    labels.extend(_safe_list(analysis.get('allergens')))
    ingredient_analysis = analysis.get('ingredient_analysis', {}) or {}
    labels.extend(_safe_list(ingredient_analysis.get('allergen_hits')))
    lowered = []
    for label in labels:
        text = str(label or '').strip()
        if text:
            lowered.append(text)
    return _dedupe_strings(lowered)


def _collect_analysis_flags(analysis: Dict[str, Any]) -> List[str]:
    flags: List[str] = []
    flags.extend(_safe_list(analysis.get('unknown_flags')))
    ingredient_analysis = analysis.get('ingredient_analysis', {}) or {}
    flags.extend(_safe_list(ingredient_analysis.get('flags')))
    for item in _collect_ingredient_items(analysis):
        flags.extend(_safe_list(item.get('flags')))
    flags.extend(_safe_list((analysis.get('processing_analysis') or {}).get('flags')))
    flags.extend(_safe_list((analysis.get('sugar_analysis') or {}).get('flags')))
    return _dedupe_strings([_lower(flag) for flag in flags])


def _match_pattern(value: Any, pattern: Any, match_type: str) -> bool:
    candidate = _lower(value)
    target = _lower(pattern)
    if not candidate or not target:
        return False
    if match_type == 'exact':
        return candidate == target
    return target in candidate


def _build_trigger(
    *,
    rule: Dict[str, Any],
    ingredient: Optional[str] = None,
    normalized: Optional[str] = None,
    category: Optional[str] = None,
    matched_value: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        'ingredient': ingredient,
        'normalized': normalized,
        'category': category,
        'source': rule.get('source'),
        'match_type': rule.get('match_type', 'contains'),
        'matched_value': matched_value,
        'impact': RESULT_LABEL.get(_lower(rule.get('impact')), 'Unknown'),
        'reason': str(rule.get('reason') or 'Matched a condition rule.'),
        'flags': _dedupe_strings([str(flag) for flag in rule.get('flags', [])]),
    }


def _match_rule(
    rule: Dict[str, Any],
    product: Optional[Dict[str, Any]],
    analysis: Dict[str, Any],
    ingredient_items: List[Dict[str, Any]],
    allergen_labels: List[str],
    analysis_flags: List[str],
) -> List[Dict[str, Any]]:
    source = _lower(rule.get('source'))
    pattern = rule.get('pattern')
    match_type = _lower(rule.get('match_type') or 'contains')
    triggers: List[Dict[str, Any]] = []

    if source == 'ingredient':
        for item in ingredient_items:
            raw = item.get('ingredient')
            normalized = item.get('normalized')
            if _match_pattern(normalized, pattern, match_type) or _match_pattern(raw, pattern, match_type):
                triggers.append(
                    _build_trigger(
                        rule=rule,
                        ingredient=str(raw or ''),
                        normalized=str(normalized or ''),
                        category=str(item.get('category') or ''),
                        matched_value=str(pattern or ''),
                    )
                )
    elif source == 'category':
        for item in ingredient_items:
            category = item.get('category')
            if _match_pattern(category, pattern, match_type):
                triggers.append(
                    _build_trigger(
                        rule=rule,
                        ingredient=str(item.get('ingredient') or ''),
                        normalized=str(item.get('normalized') or ''),
                        category=str(category or ''),
                        matched_value=str(pattern or ''),
                    )
                )
    elif source == 'allergen':
        for label in allergen_labels:
            if _match_pattern(label, pattern, match_type):
                triggers.append(
                    _build_trigger(
                        rule=rule,
                        ingredient=str(label),
                        normalized=_lower(label),
                        category='allergen',
                        matched_value=str(pattern or ''),
                    )
                )
    elif source == 'analysis_flag':
        for flag in analysis_flags:
            if _match_pattern(flag, pattern, match_type):
                triggers.append(
                    _build_trigger(
                        rule=rule,
                        ingredient=str(flag),
                        normalized=_lower(flag),
                        category='analysis-flag',
                        matched_value=str(pattern or ''),
                    )
                )
    elif source == 'subcategory':
        subcategory = (product or {}).get('subcategory') or analysis.get('subcategory')
        if _match_pattern(subcategory, pattern, match_type):
            triggers.append(
                _build_trigger(
                    rule=rule,
                    ingredient=str(subcategory or ''),
                    normalized=_lower(subcategory),
                    category='subcategory',
                    matched_value=str(pattern or ''),
                )
            )
    elif source == 'name':
        name = (product or {}).get('name') or analysis.get('name')
        if _match_pattern(name, pattern, match_type):
            triggers.append(
                _build_trigger(
                    rule=rule,
                    ingredient=str(name or ''),
                    normalized=_lower(name),
                    category='name',
                    matched_value=str(pattern or ''),
                )
            )

    return triggers


def _dedupe_triggers(triggers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    unique: List[Dict[str, Any]] = []
    for trigger in triggers:
        key = (
            trigger.get('ingredient'),
            trigger.get('normalized'),
            trigger.get('category'),
            trigger.get('source'),
            trigger.get('impact'),
            trigger.get('reason'),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(trigger)
    return unique


def _has_ambiguous_unknowns(ingredient_items: List[Dict[str, Any]]) -> bool:
    for item in ingredient_items:
        category = _lower(item.get('category'))
        flags = {_lower(flag) for flag in _safe_list(item.get('flags'))}
        if 'unknown_ingredient_flag' in flags and category in AMBIGUOUS_CATEGORIES:
            return True
    return False


def _build_summary(
    condition_name: str,
    meta: Dict[str, Any],
    result_key: str,
    triggers: List[Dict[str, Any]],
    unknown_reasons: List[str],
) -> str:
    if result_key == 'safe':
        return str(meta.get('safe_summary') or f'No {condition_name} trigger found in the verified ingredients.')
    if result_key == 'unknown':
        if unknown_reasons:
            return unknown_reasons[0]
        return str(meta.get('unknown_summary') or f'Insufficient verified data to assess {condition_name}.')
    if not triggers:
        return str(meta.get('safe_summary') or '')
    if len(triggers) == 1:
        return str(triggers[0].get('reason') or '')
    return f"{triggers[0].get('reason') or ''} {len(triggers) - 1} more trigger(s) matched."


def _build_explanation(triggers: List[Dict[str, Any]], unknown_reasons: List[str], summary: str) -> str:
    reasons = _dedupe_strings([str(trigger.get('reason') or '') for trigger in triggers] + unknown_reasons)
    if not reasons:
        return summary
    return ' '.join(reasons)


def _build_suggestions(meta: Dict[str, Any], result_key: str) -> List[str]:
    suggestions = meta.get('suggestions', {}) or {}
    values = suggestions.get(result_key, []) or []
    return _dedupe_strings([str(item) for item in values])


def _evaluate_condition(
    condition_name: str,
    product: Optional[Dict[str, Any]],
    analysis: Dict[str, Any],
) -> Dict[str, Any]:
    meta = _supported_conditions().get(condition_name, {})
    rules = _load_rule_sets().get(condition_name, [])
    ingredient_items = _collect_ingredient_items(analysis)
    allergen_labels = _collect_allergen_labels(product, analysis)
    analysis_flags = _collect_analysis_flags(analysis)

    all_triggers: List[Dict[str, Any]] = []
    for rule in rules:
        all_triggers.extend(
            _match_rule(
                rule=rule,
                product=product,
                analysis=analysis,
                ingredient_items=ingredient_items,
                allergen_labels=allergen_labels,
                analysis_flags=analysis_flags,
            )
        )

    all_triggers = _dedupe_triggers(all_triggers)
    avoid_triggers = [trigger for trigger in all_triggers if _lower(trigger.get('impact')) == 'avoid']
    caution_triggers = [trigger for trigger in all_triggers if _lower(trigger.get('impact')) == 'caution']
    unknown_triggers = [trigger for trigger in all_triggers if _lower(trigger.get('impact')) == 'unknown']

    unknown_reasons: List[str] = []
    flags: List[str] = []

    if not ingredient_items and meta.get('unknown_if_missing_ingredients', True):
        unknown_reasons.append(
            str(meta.get('unknown_summary') or 'Insufficient verified ingredient data for this health check.')
        )
        flags.append('missing_ingredients_flag')

    if not avoid_triggers and not caution_triggers and unknown_triggers:
        unknown_reasons.extend([str(trigger.get('reason') or '') for trigger in unknown_triggers])

    if not avoid_triggers and not caution_triggers and meta.get('unknown_if_ambiguous') and _has_ambiguous_unknowns(ingredient_items):
        unknown_reasons.append(
            str(
                meta.get('ambiguous_summary')
                or 'Generic ingredient wording leaves this condition check uncertain.'
            )
        )
        flags.append('ambiguous_ingredient_flag')

    if avoid_triggers:
        result_key = 'avoid'
        result_triggers = avoid_triggers
    elif caution_triggers:
        result_key = 'caution'
        result_triggers = caution_triggers
    elif unknown_reasons:
        result_key = 'unknown'
        result_triggers = unknown_triggers
    else:
        result_key = 'safe'
        result_triggers = []

    for trigger in result_triggers:
        flags.extend(_safe_list(trigger.get('flags')))

    summary = _build_summary(condition_name, meta, result_key, result_triggers, unknown_reasons)
    explanation = _build_explanation(result_triggers, unknown_reasons, summary)

    return {
        'condition': condition_name,
        'display_name': str(meta.get('display_name') or condition_name.title()),
        'kind': str(meta.get('kind') or 'condition'),
        'result': RESULT_LABEL[result_key],
        'summary': summary,
        'explanation': explanation,
        'triggers': result_triggers,
        'flags': _dedupe_strings([str(flag) for flag in flags]),
        'suggestions': _build_suggestions(meta, result_key),
    }


def build_condition_results(
    analysis: Dict[str, Any],
    allergies: Optional[List[str]] = None,
    conditions: Optional[List[str]] = None,
    product: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    requested_allergies = normalise_requested_allergies(allergies)
    requested_conditions = normalise_requested_conditions(conditions)

    if not requested_allergies and not requested_conditions:
        return {
            'requested_allergies': [],
            'requested_conditions': [],
            'condition_results': {},
            'personal_warnings': [],
        }

    results: Dict[str, Dict[str, Any]] = {}
    personal_warnings: List[str] = []

    for key in requested_allergies + requested_conditions:
        result = _evaluate_condition(key, product=product, analysis=analysis)
        results[key] = result
        if result.get('result') != 'Safe':
            personal_warnings.append(f"{result.get('display_name')}: {result.get('summary')}")

    return {
        'requested_allergies': requested_allergies,
        'requested_conditions': requested_conditions,
        'condition_results': results,
        'personal_warnings': _dedupe_strings(personal_warnings),
    }


def apply_conditions(
    analysis: Dict[str, Any],
    allergies: Optional[List[str]],
    conditions: Optional[List[str]],
    product: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    updated = dict(analysis or {})
    bundle = build_condition_results(
        analysis=updated,
        allergies=allergies,
        conditions=conditions,
        product=product,
    )

    existing_personal = _dedupe_strings([str(item) for item in _safe_list(updated.get('personal_warnings'))])
    updated['requested_allergies'] = bundle['requested_allergies']
    updated['requested_conditions'] = bundle['requested_conditions']
    updated['condition_results'] = bundle['condition_results']
    updated['personal_warnings'] = _dedupe_strings(existing_personal + bundle['personal_warnings'])
    return updated
