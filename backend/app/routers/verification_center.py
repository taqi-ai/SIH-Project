from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models import Verification, User
from app.security import get_current_user
from app.connectors.sandbox import CONNECTOR_REGISTRY

router = APIRouter(prefix="/verification-center", tags=["verification-center"])


@router.get("/connectors")
def list_connectors(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    out = []
    for code, connector in CONNECTOR_REGISTRY.items():
        last = db.query(Verification).filter(Verification.connector_code == code).order_by(desc(Verification.checked_at)).first()
        health = connector.health_check()
        out.append({
            **health,
            "last_checked": last.checked_at if last else None,
            "last_status": last.status if last else None,
            "last_response": last.response_payload if last else None,
            "total_checks": db.query(Verification).filter(Verification.connector_code == code).count(),
        })
    return out
