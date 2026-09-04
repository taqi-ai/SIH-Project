from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Tender, TenderRequirement, Bid, User
from app.security import get_current_user
from app.schemas import TenderCreate
from app.serializers import s_tender, s_requirement, s_bid
from app.rules.requirements_catalog import DEFAULT_REQUIREMENTS
from app.audit_chain import record_event

router = APIRouter(prefix="/tenders", tags=["tenders"])


@router.get("")
def list_tenders(status: str | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(Tender)
    if status:
        q = q.filter(Tender.status == status)
    tenders = q.order_by(Tender.published_date.desc()).all()
    out = []
    for t in tenders:
        row = s_tender(t)
        risks = [b.risk_level for b in t.bids if b.risk_level]
        row["max_risk"] = "HIGH" if "HIGH" in risks else ("MEDIUM" if "MEDIUM" in risks else ("LOW" if risks else None))
        out.append(row)
    return out


@router.post("")
def create_tender(payload: TenderCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    tender = Tender(**payload.model_dump())
    db.add(tender)
    db.commit()
    db.refresh(tender)
    for r in DEFAULT_REQUIREMENTS:
        db.add(TenderRequirement(
            tender_id=tender.id, code=r["code"], label=r["label"],
            document_type=r["document_type"], mandatory=r["mandatory"], rule_definition=r["rule_definition"],
        ))
    db.commit()
    record_event(db, user.email, "TENDER_CREATED", "Tender", tender.id, tender_id=tender.id, new_state=tender.title)
    return s_tender(tender)


@router.get("/{tender_id}")
def get_tender(tender_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(404, "Tender not found")
    out = s_tender(tender)
    out["requirements"] = [s_requirement(r) for r in tender.requirements]
    out["bids"] = [s_bid(b) for b in tender.bids]
    return out
