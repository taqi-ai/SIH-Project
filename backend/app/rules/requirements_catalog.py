"""Default requirement catalog attached to every new tender.
Each entry is data-driven — the compliance engine never hard-codes logic in the frontend."""

DEFAULT_REQUIREMENTS = [
    {
        "code": "UDYAM", "label": "Udyam / MSME Registration", "mandatory": True,
        "document_type": "UDYAM_CERTIFICATE",
        "rule_definition": {"type": "document_exists", "field": "document_present"},
    },
    {
        "code": "GST", "label": "GST Registration", "mandatory": True,
        "document_type": "GST_CERTIFICATE",
        "rule_definition": {"type": "expiry_after", "field": "gst_valid_upto", "compare_to": "tender_close_date"},
    },
    {
        "code": "PAN", "label": "PAN / Income Tax Identity", "mandatory": True,
        "document_type": "PAN_CARD",
        "rule_definition": {"type": "exact_match", "field_a": "bidder_pan", "field_b": "gst_pan"},
    },
    {
        "code": "INCOME_TAX", "label": "Income Tax Return", "mandatory": True,
        "document_type": "INCOME_TAX_RETURN",
        "rule_definition": {"type": "threshold", "field": "declared_turnover", "operator": ">=", "threshold_field": "min_turnover"},
    },
    {
        "code": "MII", "label": "Make in India / Local Content", "mandatory": True,
        "document_type": "MII_DECLARATION",
        "rule_definition": {"type": "threshold", "field": "local_content_pct", "operator": ">=", "threshold_field": "min_local_content_pct"},
    },
    {
        "code": "EPFO", "label": "EPFO Registration", "mandatory": True,
        "document_type": "EPFO_CERTIFICATE",
        "rule_definition": {"type": "boolean_equals", "field": "epfo_active", "expected": True},
    },
    {
        "code": "ESIC", "label": "ESIC Registration", "mandatory": True,
        "document_type": "ESIC_CERTIFICATE",
        "rule_definition": {"type": "boolean_equals", "field": "esic_active", "expected": True},
    },
    {
        "code": "STARTUP_INDIA", "label": "Startup India Recognition", "mandatory": False,
        "document_type": "STARTUP_INDIA_CERTIFICATE",
        "rule_definition": {"type": "applicable_if", "field": "is_startup", "equals": True},
    },
    {
        "code": "NSIC", "label": "NSIC Registration", "mandatory": False,
        "document_type": "NSIC_CERTIFICATE",
        "rule_definition": {"type": "applicable_if", "field": "claims_nsic_exemption", "equals": True},
    },
    {
        "code": "OEM", "label": "OEM Authorization", "mandatory": True,
        "document_type": "OEM_AUTHORIZATION",
        "rule_definition": {"type": "document_exists", "field": "document_present"},
    },
    {
        "code": "DIGILOCKER", "label": "DigiLocker Document Verification", "mandatory": True,
        "document_type": None,
        "rule_definition": {"type": "boolean_equals", "field": "digilocker_verified", "expected": True},
    },
    {
        "code": "DEBARMENT", "label": "Blacklisting / Debarment Check", "mandatory": True,
        "document_type": None,
        "rule_definition": {"type": "boolean_equals", "field": "blacklisted", "expected": False},
    },
    {
        "code": "TENDER_SPECIFIC", "label": "Tender-Specific Compliance", "mandatory": True,
        "document_type": "TENDER_SPECIFIC",
        "rule_definition": {"type": "threshold", "field": "years_in_operation", "operator": ">=", "threshold_field": "min_years_operation"},
    },
]

DOC_TYPE_TO_CODE = {r["document_type"]: r["code"] for r in DEFAULT_REQUIREMENTS if r["document_type"]}
