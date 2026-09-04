from app.models import Document, ExtractedField, Bid, Verification


def _num(value):
    if value is None:
        return None
    try:
        return float(str(value).replace(",", "").strip())
    except ValueError:
        return None


def build_extracted_facts(bid: Bid, db) -> dict:
    """Merge all extracted fields across a bid's processed documents into one facts dict.
    Later documents don't silently overwrite earlier ones for identity fields — first non-null wins,
    keeping the earliest confidently-extracted value as canonical."""
    facts: dict = {}
    docs = db.query(Document).filter(Document.bid_id == bid.id).all()
    doc_by_type = {}
    for doc in docs:
        doc_by_type.setdefault(doc.document_type, doc)
        fields = db.query(ExtractedField).filter(ExtractedField.document_id == doc.id).all()
        for f in fields:
            if f.field_name not in facts:
                facts[f.field_name] = f.field_value

    if "gst_gstin" in facts and len(facts["gst_gstin"]) >= 12:
        facts["gst_pan"] = facts["gst_gstin"][2:12]

    facts["declared_turnover"] = _num(facts.get("declared_turnover")) or bid.declared_turnover
    facts["local_content_pct"] = _num(facts.get("local_content_pct")) or bid.declared_local_content_pct
    facts["years_in_operation"] = _num(facts.get("years_in_operation"))

    facts["company_name"] = facts.get("company_name") or bid.bidder.company_name
    facts["is_startup"] = "STARTUP_INDIA_CERTIFICATE" in doc_by_type
    facts["claims_nsic_exemption"] = "NSIC_CERTIFICATE" in doc_by_type
    facts["document_count"] = len(docs)
    facts["_doc_by_type"] = doc_by_type
    return facts


def apply_verification_facts(facts: dict, verifications: list[Verification]) -> dict:
    by_code = {v.connector_code: v for v in verifications}

    def status_of(code):
        v = by_code.get(code)
        return v.status if v else None

    facts["udyam_valid"] = status_of("UDYAM") == "VERIFIED"
    facts["gstin_active"] = status_of("GSTN") == "VERIFIED"
    it = by_code.get("INCOME_TAX")
    facts["pan_valid"] = (it.response_payload.get("pan_status") == "Active") if it else None
    facts["itr_filed"] = it.response_payload.get("itr_filed", True) if it else None
    facts["epfo_active"] = status_of("EPFO") == "VERIFIED"
    facts["esic_active"] = status_of("ESIC") == "VERIFIED"
    facts["digilocker_verified"] = status_of("DIGILOCKER") == "VERIFIED"
    deb = by_code.get("DEBARMENT")
    facts["blacklisted"] = bool(deb.response_payload.get("listed")) if deb else False
    return facts
