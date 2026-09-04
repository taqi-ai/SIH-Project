import hashlib
import json
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models import AuditEvent

GENESIS_HASH = "0" * 64


def _hash_event(prev_hash: str, payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256((prev_hash + canonical).encode("utf-8")).hexdigest()


def record_event(
    db: Session,
    actor: str,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    bid_id: str | None = None,
    tender_id: str | None = None,
    previous_state: str | None = None,
    new_state: str | None = None,
    evidence_reference: str | None = None,
) -> AuditEvent:
    """Append-only, SHA-256 hash-chained audit event (audit-ready tamper-evident event chain)."""
    last = db.query(AuditEvent).order_by(desc(AuditEvent.timestamp)).first()
    prev_hash = last.event_hash if last else GENESIS_HASH

    payload = {
        "actor": actor,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "bid_id": bid_id,
        "tender_id": tender_id,
        "previous_state": previous_state,
        "new_state": new_state,
    }
    event_hash = _hash_event(prev_hash, payload)

    event = AuditEvent(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        bid_id=bid_id,
        tender_id=tender_id,
        previous_state=previous_state,
        new_state=new_state,
        evidence_reference=evidence_reference,
        prev_hash=prev_hash,
        event_hash=event_hash,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def verify_chain(db: Session) -> dict:
    """Recomputes the hash chain to confirm no event has been tampered with."""
    events = db.query(AuditEvent).order_by(AuditEvent.timestamp).all()
    prev_hash = GENESIS_HASH
    for e in events:
        payload = {
            "actor": e.actor,
            "action": e.action,
            "entity_type": e.entity_type,
            "entity_id": e.entity_id,
            "bid_id": e.bid_id,
            "tender_id": e.tender_id,
            "previous_state": e.previous_state,
            "new_state": e.new_state,
        }
        expected = _hash_event(prev_hash, payload)
        if expected != e.event_hash or e.prev_hash != prev_hash:
            return {"valid": False, "broken_at_event": e.id, "total_events": len(events)}
        prev_hash = e.event_hash
    return {"valid": True, "total_events": len(events)}
