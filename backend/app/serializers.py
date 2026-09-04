def s_tender(t):
    return {
        "id": t.id, "tender_number": t.tender_number, "title": t.title, "organization": t.organization,
        "category": t.category, "estimated_value": t.estimated_value,
        "published_date": t.published_date, "closing_date": t.closing_date, "status": t.status,
        "description": t.description, "min_turnover": t.min_turnover,
        "min_years_operation": t.min_years_operation, "min_local_content_pct": t.min_local_content_pct,
        "requires_oem_authorization": t.requires_oem_authorization,
        "bid_count": len(t.bids),
    }


def s_requirement(r):
    return {
        "id": r.id, "code": r.code, "label": r.label, "document_type": r.document_type,
        "mandatory": r.mandatory, "rule_definition": r.rule_definition, "applicable": r.applicable,
    }


def s_bidder(b):
    return {
        "id": b.id, "company_name": b.company_name, "pan": b.pan, "gstin": b.gstin, "cin": b.cin,
        "udyam_number": b.udyam_number, "address": b.address, "contact_email": b.contact_email,
        "contact_phone": b.contact_phone, "enterprise_type": b.enterprise_type,
        "incorporation_year": b.incorporation_year,
    }


def s_bid(bid, include_tender=False):
    out = {
        "id": bid.id, "tender_id": bid.tender_id, "bidder": s_bidder(bid.bidder), "status": bid.status,
        "submitted_at": bid.submitted_at, "declared_turnover": bid.declared_turnover,
        "declared_local_content_pct": bid.declared_local_content_pct,
        "compliance_score": bid.compliance_score, "risk_level": bid.risk_level,
        "final_decision": bid.final_decision, "final_decision_reason": bid.final_decision_reason,
        "final_decision_by": bid.final_decision_by, "final_decision_at": bid.final_decision_at,
        "document_count": len(bid.documents),
    }
    if include_tender:
        out["tender"] = s_tender(bid.tender)
    return out


def s_document(d):
    return {
        "id": d.id, "bid_id": d.bid_id, "document_type": d.document_type,
        "original_filename": d.original_filename, "mime_type": d.mime_type, "size_bytes": d.size_bytes,
        "page_count": d.page_count, "status": d.status, "uploaded_at": d.uploaded_at,
        "processed_at": d.processed_at, "processing_log": d.processing_log,
        "extracted_fields": [s_field(f) for f in d.extracted_fields],
    }


def s_field(f):
    return {
        "id": f.id, "field_name": f.field_name, "field_value": f.field_value,
        "confidence": f.confidence, "page": f.page, "source": f.source, "bounding_box": f.bounding_box,
    }


def s_verification(v):
    return {
        "id": v.id, "connector_code": v.connector_code, "connector_label": v.connector_label,
        "status": v.status, "response_payload": v.response_payload, "source_label": v.source_label,
        "checked_at": v.checked_at, "latency_ms": v.latency_ms,
    }


def s_evaluation(e):
    return {
        "id": e.id, "requirement": s_requirement(e.requirement), "status": e.status,
        "evidence_document_id": e.evidence_document_id, "confidence": e.confidence,
        "rule_trace": e.rule_trace, "finding_summary": e.finding_summary,
        "officer_status": e.officer_status, "evaluated_at": e.evaluated_at,
    }


def s_finding(f):
    return {
        "id": f.id, "bid_id": f.bid_id, "finding_type": f.finding_type, "title": f.title,
        "severity": f.severity, "description": f.description,
        "evidence_document_id": f.evidence_document_id, "evidence_page": f.evidence_page,
        "compared_document_id": f.compared_document_id, "compared_page": f.compared_page,
        "field_a": f.field_a, "field_b": f.field_b, "value_a": f.value_a, "value_b": f.value_b,
        "similarity": f.similarity, "confidence": f.confidence, "recommendation": f.recommendation,
        "status": f.status, "created_at": f.created_at,
    }


def s_risk(r):
    if not r:
        return None
    return {
        "overall_score": r.overall_score, "risk_level": r.risk_level,
        "document_completeness_pct": r.document_completeness_pct,
        "registry_verification_pct": r.registry_verification_pct,
        "tender_compliance_pct": r.tender_compliance_pct, "consistency_pct": r.consistency_pct,
        "risk_factors": r.risk_factors, "computed_at": r.computed_at,
    }


def s_review(r):
    return {
        "id": r.id, "bid_id": r.bid_id, "finding_id": r.finding_id,
        "requirement_evaluation_id": r.requirement_evaluation_id, "officer_id": r.officer_id,
        "action": r.action, "comment": r.comment, "justification": r.justification,
        "previous_state": r.previous_state, "new_state": r.new_state, "created_at": r.created_at,
    }


def s_audit(a):
    return {
        "id": a.id, "bid_id": a.bid_id, "tender_id": a.tender_id, "actor": a.actor, "action": a.action,
        "entity_type": a.entity_type, "entity_id": a.entity_id, "previous_state": a.previous_state,
        "new_state": a.new_state, "evidence_reference": a.evidence_reference, "timestamp": a.timestamp,
        "prev_hash": a.prev_hash, "event_hash": a.event_hash,
    }
