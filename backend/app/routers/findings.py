from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ComplianceFinding, ComplianceEvaluation, OfficerReview, User
from app.security import get_current_user
from app.schemas import ReviewCreate
from app.serializers import s_review, s_finding, s_evaluation
from app.audit_chain import record_event

router = APIRouter(tags=["findings"])

ACTIONS_REQUIRING_JUSTIFICATION = {"OVERRIDE"}


@router.post("/findings/{finding_id}/review")
def review_finding(finding_id: str, payload: ReviewCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    finding = db.query(ComplianceFinding).filter(ComplianceFinding.id == finding_id).first()
    if not finding:
        raise HTTPException(404, "Finding not found")
    return _apply_review(db, user, bid_id=finding.bid_id, finding=finding, evaluation=None, payload=payload)


@router.post("/findings/{finding_id}/override")
def override_finding(finding_id: str, payload: ReviewCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    finding = db.query(ComplianceFinding).filter(ComplianceFinding.id == finding_id).first()
    if not finding:
        raise HTTPException(404, "Finding not found")
    payload.action = "OVERRIDE"
    return _apply_review(db, user, bid_id=finding.bid_id, finding=finding, evaluation=None, payload=payload)


@router.post("/evaluations/{evaluation_id}/review")
def review_evaluation(evaluation_id: str, payload: ReviewCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    evaluation = db.query(ComplianceEvaluation).filter(ComplianceEvaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(404, "Requirement evaluation not found")
    return _apply_review(db, user, bid_id=evaluation.bid_id, finding=None, evaluation=evaluation, payload=payload)


def _apply_review(db: Session, user: User, bid_id: str, finding, evaluation, payload: ReviewCreate):
    if payload.action in ACTIONS_REQUIRING_JUSTIFICATION and not (payload.justification and len(payload.justification.strip()) >= 5):
        raise HTTPException(400, "A justification is mandatory when overriding an AI finding or requirement status")

    previous_state, new_state = None, None

    if finding:
        previous_state = finding.status
        if payload.action == "ACCEPT_FINDING":
            finding.status = "ACCEPTED"
        elif payload.action == "REJECT_FINDING":
            finding.status = "REJECTED"
        elif payload.action == "REQUEST_CLARIFICATION":
            finding.status = "CLARIFICATION_REQUESTED"
        elif payload.action == "OVERRIDE":
            finding.status = "REJECTED"
        new_state = finding.status

    if evaluation:
        previous_state = evaluation.status
        if payload.action == "MARK_VERIFIED":
            evaluation.officer_status = "VERIFIED"
        elif payload.action == "MARK_FAILED":
            evaluation.officer_status = "FAILED"
        elif payload.action == "OVERRIDE":
            evaluation.officer_status = payload.comment.split(":")[0].strip().upper() if payload.comment else "VERIFIED"
        new_state = evaluation.officer_status

    review = OfficerReview(
        bid_id=bid_id, finding_id=finding.id if finding else None,
        requirement_evaluation_id=evaluation.id if evaluation else None,
        officer_id=user.id, action=payload.action, comment=payload.comment,
        justification=payload.justification, previous_state=previous_state, new_state=new_state,
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    action_label = "OFFICER_OVERRIDE" if payload.action == "OVERRIDE" else "OFFICER_REVIEWED_FINDING"
    record_event(
        db, user.email, action_label,
        "ComplianceFinding" if finding else "ComplianceEvaluation",
        finding.id if finding else evaluation.id, bid_id=bid_id,
        previous_state=previous_state, new_state=new_state,
        evidence_reference=(finding.evidence_document_id if finding else evaluation.evidence_document_id),
    )
    return s_review(review)
