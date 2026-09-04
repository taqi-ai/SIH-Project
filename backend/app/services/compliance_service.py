from datetime import datetime
from sqlalchemy.orm import Session

from app.models import (
    Bid, TenderRequirement, ComplianceEvaluation, ComplianceFinding, Document, RiskAssessment, Verification
)
from app.rules.engine import evaluate_rule
from app.services.facts_builder import build_extracted_facts, apply_verification_facts
from app.services.verification_service import run_verifications
from app.ai.service import ai_service
from app.audit_chain import record_event


def evaluate_bid(bid_id: str, db: Session, actor: str = "SYSTEM_COMPLIANCE_ENGINE") -> dict:
    bid = db.query(Bid).filter(Bid.id == bid_id).first()
    if not bid:
        raise ValueError("Bid not found")

    verifications = run_verifications(bid_id, db, actor="SYSTEM_CONNECTORS")

    facts = build_extracted_facts(bid, db)
    doc_by_type = facts.pop("_doc_by_type", {})
    facts["min_turnover"] = bid.tender.min_turnover
    facts["min_local_content_pct"] = bid.tender.min_local_content_pct
    facts["min_years_operation"] = bid.tender.min_years_operation
    facts["tender_close_date"] = bid.tender.closing_date
    facts = apply_verification_facts(facts, verifications)

    db.query(ComplianceEvaluation).filter(ComplianceEvaluation.bid_id == bid_id).delete()
    requirements = db.query(TenderRequirement).filter(TenderRequirement.tender_id == bid.tender_id).all()

    evaluations = []
    for req in requirements:
        evidence_doc = doc_by_type.get(req.document_type) if req.document_type else None
        if not req.applicable:
            from app.rules.engine import RuleResult
            result = RuleResult("NOT_APPLICABLE", {"reason": "requirement not applicable to this tender"})
        else:
            req_facts = dict(facts)
            req_facts["document_present"] = evidence_doc is not None
            result = evaluate_rule(req.rule_definition, req_facts)

        confidence = None
        if evidence_doc:
            confs = [f.confidence for f in evidence_doc.extracted_fields] if evidence_doc.extracted_fields else []
            confidence = round(sum(confs) / len(confs), 3) if confs else 0.5

        eval_row = ComplianceEvaluation(
            bid_id=bid_id,
            requirement_id=req.id,
            status=result.status,
            evidence_document_id=evidence_doc.id if evidence_doc else None,
            confidence=confidence,
            rule_trace=result.trace,
            finding_summary=result.trace.get("reason"),
            evaluated_at=datetime.utcnow(),
        )
        db.add(eval_row)
        evaluations.append(eval_row)
    db.commit()
    record_event(db, actor, "RULE_EXECUTED", "Bid", bid_id, bid_id=bid_id,
                 new_state=f"{len(evaluations)} requirements evaluated")

    # --- AI: cross-document contradiction detection ---
    db.query(ComplianceFinding).filter(
        ComplianceFinding.bid_id == bid_id, ComplianceFinding.finding_type == "CONTRADICTION"
    ).delete()
    docs = db.query(Document).filter(Document.bid_id == bid_id).all()
    fields_by_document = []
    for doc in docs:
        field_map = {f.field_name: f.field_value for f in doc.extracted_fields}
        if field_map:
            fields_by_document.append({
                "document_id": doc.id, "document_type": doc.document_type,
                "filename": doc.original_filename, "fields": field_map,
            })
    contradictions = ai_service.detect_contradictions(fields_by_document)
    for c in contradictions:
        db.add(ComplianceFinding(bid_id=bid_id, **c))
    if contradictions:
        record_event(db, "SYSTEM_AI", "AI_FINDING_GENERATED", "Bid", bid_id, bid_id=bid_id,
                     new_state=f"{len(contradictions)} contradiction(s) detected")

    # --- missing mandatory document findings ---
    db.query(ComplianceFinding).filter(
        ComplianceFinding.bid_id == bid_id, ComplianceFinding.finding_type == "MISSING_INFO"
    ).delete()
    for req, ev in zip(requirements, evaluations):
        if req.mandatory and ev.status == "FAILED" and req.rule_definition.get("type") == "document_exists":
            db.add(ComplianceFinding(
                bid_id=bid_id, finding_type="MISSING_INFO", title=f"Missing mandatory document: {req.label}",
                severity="HIGH", description=f"No document was uploaded/matched for requirement '{req.label}'.",
                confidence=1.0, recommendation="Request the missing document from the bidder before qualification.",
            ))
    db.commit()

    risk = compute_risk(bid_id, db)
    bid.compliance_score = risk.overall_score
    bid.risk_level = risk.risk_level
    bid.status = "EVALUATED"
    db.commit()
    record_event(db, actor, "COMPLIANCE_SCORE_CHANGED", "Bid", bid_id, bid_id=bid_id,
                 new_state=f"score={risk.overall_score}, risk={risk.risk_level}")

    return {"evaluations": evaluations, "risk": risk}


def compute_risk(bid_id: str, db: Session) -> RiskAssessment:
    evaluations = db.query(ComplianceEvaluation).filter(ComplianceEvaluation.bid_id == bid_id).all()
    findings = db.query(ComplianceFinding).filter(ComplianceFinding.bid_id == bid_id, ComplianceFinding.status == "OPEN").all()
    documents = db.query(Document).filter(Document.bid_id == bid_id).all()

    applicable = [e for e in evaluations if e.status != "NOT_APPLICABLE"]
    verified = [e for e in applicable if e.status == "VERIFIED"]
    failed = [e for e in applicable if e.status == "FAILED"]
    warnings = [e for e in applicable if e.status == "WARNING"]

    document_completeness_pct = round(100 * (1 - (len([d for d in documents if d.status == "FAILED"]) / max(len(documents), 1))), 1) if documents else 0
    registry_verification_pct = round(100 * len(verified) / max(len(applicable), 1), 1) if applicable else 0
    tender_compliance_pct = round(100 * (len(verified) + 0.5 * len(warnings)) / max(len(applicable), 1), 1) if applicable else 0
    consistency_pct = round(max(0, 100 - 15 * len(findings)), 1)

    score = 100.0
    risk_factors = []
    for e in failed:
        score -= 15
        risk_factors.append(f"{e.requirement.label}: {e.finding_summary or 'requirement failed'}")
    for e in warnings:
        score -= 6
        risk_factors.append(f"{e.requirement.label}: flagged for review — {e.finding_summary or ''}".strip())
    for f in findings:
        score -= 10 if f.severity in ("HIGH", "CRITICAL") else 5
        risk_factors.append(f.title)
    score = max(0, round(score, 1))

    if score >= 92 and not any(e.status == "FAILED" for e in evaluations):
        risk_level = "LOW"
    elif score >= 55 and not any(e.status == "FAILED" for e in evaluations):
        risk_level = "MEDIUM"
    elif score >= 40:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    db.query(RiskAssessment).filter(RiskAssessment.bid_id == bid_id).delete()
    risk = RiskAssessment(
        bid_id=bid_id, overall_score=score, risk_level=risk_level,
        document_completeness_pct=document_completeness_pct,
        registry_verification_pct=registry_verification_pct,
        tender_compliance_pct=tender_compliance_pct,
        consistency_pct=consistency_pct,
        risk_factors=risk_factors[:8],
    )
    db.add(risk)
    db.commit()
    db.refresh(risk)
    return risk
