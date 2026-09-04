from datetime import datetime
from app.rules.engine import evaluate_rule


def test_expiry_after_pass():
    rule = {"type": "expiry_after", "field": "expiry", "compare_to": "close"}
    facts = {"expiry": "2027-01-01", "close": "2026-06-01"}
    assert evaluate_rule(rule, facts).status == "VERIFIED"


def test_expiry_after_fail():
    rule = {"type": "expiry_after", "field": "expiry", "compare_to": "close"}
    facts = {"expiry": "2026-01-01", "close": "2026-06-01"}
    assert evaluate_rule(rule, facts).status == "FAILED"


def test_expiry_missing_value_is_warning():
    rule = {"type": "expiry_after", "field": "expiry", "compare_to": "close"}
    result = evaluate_rule(rule, {"close": "2026-06-01"})
    assert result.status == "WARNING"


def test_threshold_pass():
    rule = {"type": "threshold", "field": "turnover", "operator": ">=", "threshold_field": "min_turnover"}
    facts = {"turnover": 100, "min_turnover": 50}
    assert evaluate_rule(rule, facts).status == "VERIFIED"


def test_threshold_fail_below_minimum():
    rule = {"type": "threshold", "field": "turnover", "operator": ">=", "threshold_field": "min_turnover"}
    facts = {"turnover": 30, "min_turnover": 50}
    assert evaluate_rule(rule, facts).status == "FAILED"


def test_threshold_borderline_is_warning():
    rule = {"type": "threshold", "field": "turnover", "operator": ">=", "threshold_field": "min_turnover"}
    facts = {"turnover": 101, "min_turnover": 100}
    assert evaluate_rule(rule, facts).status == "WARNING"


def test_pan_exact_match_pass():
    rule = {"type": "exact_match", "field_a": "bidder_pan", "field_b": "gst_pan"}
    facts = {"bidder_pan": "AAFCB4521K", "gst_pan": "AAFCB4521K"}
    assert evaluate_rule(rule, facts).status == "VERIFIED"


def test_pan_gst_mismatch_fails():
    rule = {"type": "exact_match", "field_a": "bidder_pan", "field_b": "gst_pan"}
    facts = {"bidder_pan": "AAFCB4521K", "gst_pan": "ZZZZZ0000Z"}
    assert evaluate_rule(rule, facts).status == "FAILED"


def test_missing_mandatory_document_fails():
    rule = {"type": "document_exists", "field": "document_present"}
    assert evaluate_rule(rule, {"document_present": False}).status == "FAILED"
    assert evaluate_rule(rule, {"document_present": True}).status == "VERIFIED"


def test_debarment_boolean_rule():
    rule = {"type": "boolean_equals", "field": "blacklisted", "expected": False}
    assert evaluate_rule(rule, {"blacklisted": False}).status == "VERIFIED"
    assert evaluate_rule(rule, {"blacklisted": True}).status == "FAILED"


def test_applicable_if_gates_not_applicable():
    rule = {"type": "applicable_if", "field": "is_startup", "equals": True}
    result = evaluate_rule(rule, {"is_startup": False})
    assert result.status == "NOT_APPLICABLE"


def test_applicable_if_requires_document_when_claimed():
    rule = {"type": "applicable_if", "field": "is_startup", "equals": True}
    result = evaluate_rule(rule, {"is_startup": True, "document_present": False})
    assert result.status == "FAILED"
    result_ok = evaluate_rule(rule, {"is_startup": True, "document_present": True})
    assert result_ok.status == "VERIFIED"
