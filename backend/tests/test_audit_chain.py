from app.database import SessionLocal
from app.audit_chain import record_event, verify_chain


def test_audit_chain_valid_after_events(setup_db):
    db = SessionLocal()
    record_event(db, "tester@test.gov.in", "TENDER_CREATED", "Tender", "TDR-TEST1", tender_id="TDR-TEST1")
    record_event(db, "tester@test.gov.in", "BID_CREATED", "Bid", "BID-TEST1", bid_id="BID-TEST1")
    result = verify_chain(db)
    db.close()
    assert result["valid"] is True


def test_audit_chain_detects_tamper(setup_db):
    db = SessionLocal()
    event = record_event(db, "tester@test.gov.in", "DOCUMENT_UPLOADED", "Document", "DOC-TEST1", bid_id="BID-TEST1")
    event.new_state = "TAMPERED_VALUE"
    db.commit()
    result = verify_chain(db)
    db.close()
    assert result["valid"] is False
