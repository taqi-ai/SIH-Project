from datetime import datetime
from sqlalchemy.orm import Session

from app.models import Bid, Verification
from app.connectors.sandbox import CONNECTOR_REGISTRY
from app.services.facts_builder import build_extracted_facts
from app.audit_chain import record_event


def run_verifications(bid_id: str, db: Session, actor: str = "SYSTEM_CONNECTORS") -> list[Verification]:
    bid = db.query(Bid).filter(Bid.id == bid_id).first()
    if not bid:
        raise ValueError("Bid not found")

    facts = build_extracted_facts(bid, db)
    facts["min_local_content_pct"] = bid.tender.min_local_content_pct

    db.query(Verification).filter(Verification.bid_id == bid_id).delete()
    db.commit()

    results = []
    for code, connector in CONNECTOR_REGISTRY.items():
        try:
            result = connector.verify(facts)
        except Exception as exc:  # connector must never crash the pipeline
            from app.connectors.base import ConnectorResult
            result = ConnectorResult("UNAVAILABLE", f"Sandbox connector error: {exc}")

        v = Verification(
            bid_id=bid_id,
            connector_code=code,
            connector_label=connector.label,
            status=result.status,
            request_payload={k: v for k, v in facts.items() if not k.startswith("_") and isinstance(v, (str, int, float, bool))},
            response_payload=result.response_payload,
            source_label=result.source_label,
            checked_at=datetime.utcnow(),
            latency_ms=result.latency_ms or 180,
        )
        db.add(v)
        results.append(v)

    db.commit()
    record_event(db, actor, "EXTERNAL_VERIFICATION_PERFORMED", "Bid", bid_id, bid_id=bid_id,
                 new_state=f"{len(results)} connectors checked")
    return results
