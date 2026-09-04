from app.ai.service import ai_service


def test_detects_pan_mismatch():
    docs = [
        {"document_id": "d1", "document_type": "PAN_CARD", "filename": "pan.pdf",
         "fields": {"bidder_pan": "AAFCB4521K"}},
        {"document_id": "d2", "document_type": "GST_CERTIFICATE", "filename": "gst.pdf",
         "fields": {"bidder_pan": "ZZZZZ0000Z"}},
    ]
    findings = ai_service.detect_contradictions(docs)
    assert any(f["field_a"] == "bidder_pan" for f in findings)


def test_no_false_positive_for_identical_names():
    docs = [
        {"document_id": "d1", "document_type": "PAN_CARD", "filename": "pan.pdf",
         "fields": {"company_name": "ABC Engineering Private Limited"}},
        {"document_id": "d2", "document_type": "GST_CERTIFICATE", "filename": "gst.pdf",
         "fields": {"company_name": "ABC Engineering Private Limited"}},
    ]
    findings = ai_service.detect_contradictions(docs)
    assert findings == []


def test_turnover_inconsistency_detected():
    docs = [
        {"document_id": "d1", "document_type": "INCOME_TAX_RETURN", "filename": "itr.pdf",
         "fields": {"declared_turnover": "10,000,000"}},
        {"document_id": "d2", "document_type": "FINANCIAL_STATEMENT", "filename": "fs.pdf",
         "fields": {"declared_turnover": "7,000,000"}},
    ]
    findings = ai_service.detect_contradictions(docs)
    turnover_findings = [f for f in findings if f["title"] == "Potential turnover inconsistency"]
    assert len(turnover_findings) == 1
    assert turnover_findings[0]["severity"] == "HIGH"


def test_minor_naming_variation_flagged_medium():
    docs = [
        {"document_id": "d1", "document_type": "UDYAM_CERTIFICATE", "filename": "udyam.pdf",
         "fields": {"company_name": "ABC Engineering Limited"}},
        {"document_id": "d2", "document_type": "GST_CERTIFICATE", "filename": "gst.pdf",
         "fields": {"company_name": "ABC Engineering Pvt. Ltd."}},
    ]
    findings = ai_service.detect_contradictions(docs)
    assert any(f["title"].startswith("Company Name mismatch") for f in findings)
