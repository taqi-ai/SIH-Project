"""Deterministic compliance rule engine.

Handles everything that can be decided with plain comparisons: dates, thresholds,
percentages, exact-match identifiers, and booleans. AI is never used here —
see app/ai/service.py for the semantic/OCR side of the pipeline.
"""
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class RuleResult:
    status: str  # VERIFIED | WARNING | FAILED | NOT_APPLICABLE | PENDING
    trace: dict = field(default_factory=dict)


def _parse_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            return datetime.strptime(str(value), fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(str(value))
    except Exception:
        return None


def _cmp(operator: str, a, b) -> bool:
    ops = {
        ">=": lambda x, y: x >= y,
        "<=": lambda x, y: x <= y,
        ">": lambda x, y: x > y,
        "<": lambda x, y: x < y,
        "==": lambda x, y: x == y,
        "!=": lambda x, y: x != y,
    }
    return ops[operator](a, b)


def evaluate_rule(rule: dict, facts: dict) -> RuleResult:
    """
    rule: data-driven rule definition, e.g.
        {"type": "document_exists", "field": "document_present"}
        {"type": "expiry_after", "field": "expiry_date", "compare_to": "tender_close_date"}
        {"type": "threshold", "field": "turnover", "operator": ">=", "threshold_field": "min_turnover"}
        {"type": "exact_match", "field_a": "bidder_pan", "field_b": "gst_pan"}
        {"type": "boolean_equals", "field": "blacklisted", "expected": False}
        {"type": "applicable_if", "field": "category", "equals": "Startup"}  -> gate, else NOT_APPLICABLE
    facts: flattened dict of extracted/verified values for one bid+requirement
    """
    rtype = rule.get("type")

    if rtype == "applicable_if":
        if facts.get(rule["field"]) != rule.get("equals"):
            return RuleResult("NOT_APPLICABLE", {"reason": "gate condition not met", "rule": rule})
        present = bool(facts.get("document_present"))
        if not present:
            return RuleResult("FAILED", {"reason": "condition claimed but supporting document missing", "rule": rule})
        return RuleResult("VERIFIED", {"reason": "condition met and document present", "rule": rule})

    if rtype == "document_exists":
        present = bool(facts.get(rule.get("field", "document_present")))
        if not present:
            return RuleResult("FAILED", {"reason": "mandatory document missing", "rule": rule})
        return RuleResult("VERIFIED", {"reason": "document present", "rule": rule})

    if rtype == "expiry_after":
        val = _parse_date(facts.get(rule["field"]))
        cmp_to = _parse_date(facts.get(rule["compare_to"]))
        if val is None:
            return RuleResult("WARNING", {"reason": "expiry date not extracted", "rule": rule})
        if cmp_to is None:
            return RuleResult("PENDING", {"reason": "comparison date unavailable", "rule": rule})
        if val < cmp_to:
            return RuleResult("FAILED", {
                "reason": "document expired before tender closing date",
                "value": str(val.date()), "compare_to": str(cmp_to.date()), "rule": rule,
            })
        return RuleResult("VERIFIED", {
            "reason": "valid beyond tender closing date",
            "value": str(val.date()), "compare_to": str(cmp_to.date()), "rule": rule,
        })

    if rtype == "threshold":
        val = facts.get(rule["field"])
        threshold = facts.get(rule["threshold_field"], rule.get("threshold"))
        if val is None:
            return RuleResult("WARNING", {"reason": f"{rule['field']} not extracted", "rule": rule})
        if threshold is None:
            return RuleResult("PENDING", {"reason": "threshold undefined", "rule": rule})
        ok = _cmp(rule["operator"], float(val), float(threshold))
        margin = float(val) - float(threshold)
        status = "VERIFIED" if ok else "FAILED"
        # flag values that pass but sit within a thin margin for officer attention
        if ok and threshold and abs(margin) / max(abs(float(threshold)), 1) < 0.05:
            status = "WARNING"
        return RuleResult(status, {
            "reason": f"{rule['field']} {rule['operator']} {rule.get('threshold_field', 'threshold')}",
            "value": val, "threshold": threshold, "margin": margin, "rule": rule,
        })

    if rtype == "exact_match":
        a = facts.get(rule["field_a"])
        b = facts.get(rule["field_b"])
        if a is None or b is None:
            return RuleResult("WARNING", {"reason": "one or both values not extracted", "rule": rule})
        norm = lambda s: str(s).strip().upper().replace(" ", "")
        ok = norm(a) == norm(b)
        return RuleResult("VERIFIED" if ok else "FAILED", {
            "reason": f"{rule['field_a']} vs {rule['field_b']}", "value_a": a, "value_b": b, "rule": rule,
        })

    if rtype == "boolean_equals":
        val = facts.get(rule["field"])
        if val is None:
            return RuleResult("PENDING", {"reason": f"{rule['field']} unavailable", "rule": rule})
        ok = bool(val) == bool(rule["expected"])
        return RuleResult("VERIFIED" if ok else "FAILED", {
            "reason": f"{rule['field']} == {rule['expected']}", "value": val, "rule": rule,
        })

    return RuleResult("PENDING", {"reason": "unrecognized rule type", "rule": rule})
