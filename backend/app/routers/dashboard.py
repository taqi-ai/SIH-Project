from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Tender, Bid, Document, Verification, User
from app.security import get_current_user
from app.serializers import s_tender

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    active_tenders = db.query(Tender).filter(Tender.status.in_(["OPEN", "UNDER_EVALUATION"])).count()
    bids_under_review = db.query(Bid).filter(Bid.status.in_(["UNDER_REVIEW", "EVALUATED", "DOCUMENTS_PENDING"])).count()
    compliant_bids = db.query(Bid).filter(Bid.final_decision == "QUALIFIED").count()
    high_risk_bids = db.query(Bid).filter(Bid.risk_level == "HIGH").count()
    pending_verification = db.query(Bid).filter(Bid.status == "DOCUMENTS_PENDING").count()
    documents_processed = db.query(Document).filter(Document.status.in_(["VERIFIED", "WARNING", "FAILED"])).count()

    total_verifications = db.query(Verification).count()
    successful_verifications = db.query(Verification).filter(Verification.status == "VERIFIED").count()
    success_rate = round(100 * successful_verifications / total_verifications, 1) if total_verifications else 0

    recent_tenders = db.query(Tender).order_by(Tender.published_date.desc()).limit(5).all()

    risk_counts = dict(
        db.query(Bid.risk_level, func.count(Bid.id)).filter(Bid.risk_level.isnot(None)).group_by(Bid.risk_level).all()
    )

    from app.models import AuditEvent
    recent_activity = db.query(AuditEvent).order_by(AuditEvent.timestamp.desc()).limit(10).all()

    return {
        "active_tenders": active_tenders,
        "bids_under_review": bids_under_review,
        "compliant_bids": compliant_bids,
        "high_risk_bids": high_risk_bids,
        "pending_verification": pending_verification,
        "documents_processed": documents_processed,
        "verification_success_rate": success_rate,
        "risk_distribution": {"LOW": risk_counts.get("LOW", 0), "MEDIUM": risk_counts.get("MEDIUM", 0), "HIGH": risk_counts.get("HIGH", 0)},
        "recent_tenders": [s_tender(t) for t in recent_tenders],
        "recent_activity": [
            {"actor": a.actor, "action": a.action, "entity_type": a.entity_type, "timestamp": a.timestamp}
            for a in recent_activity
        ],
    }
