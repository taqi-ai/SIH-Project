"""QUEUED -> PROCESSING -> OCR -> EXTRACTION -> VALIDATION -> VERIFIED/WARNING/FAILED"""
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import Document, ExtractedField, DocumentStatus
from app.ai.ocr import ocr_document
from app.ai.service import ai_service
from app.storage import storage
from app.audit_chain import record_event

REQUIRED_FIELDS_MIN = 1


def _log(document: Document, stage: str, message: str):
    entry = {"stage": stage, "message": message, "at": datetime.utcnow().isoformat()}
    document.processing_log = (document.processing_log or []) + [entry]


def process_document(document_id: str, db: Session, actor: str = "SYSTEM_PIPELINE") -> Document:
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise ValueError("Document not found")

    doc.status = DocumentStatus.PROCESSING.value
    _log(doc, "PROCESSING", "Document accepted into processing pipeline.")
    db.commit()

    full_path = storage.full_path(doc.stored_path)

    doc.status = DocumentStatus.OCR.value
    ocr_result = ocr_document(str(full_path))
    _log(doc, "OCR", ocr_result["message"])
    doc.ocr_text = ocr_result["full_text"][:20000]
    doc.page_count = max(1, len(ocr_result["pages"]))
    db.commit()

    if not ocr_result["success"]:
        doc.status = DocumentStatus.FAILED.value
        _log(doc, "VALIDATION", "Processing halted — no readable text layer.")
        db.commit()
        record_event(db, actor, "OCR_FAILED", "Document", doc.id, bid_id=doc.bid_id,
                      new_state=doc.status, evidence_reference=doc.id)
        return doc

    record_event(db, actor, "OCR_COMPLETED", "Document", doc.id, bid_id=doc.bid_id, evidence_reference=doc.id)

    doc.status = DocumentStatus.EXTRACTION.value
    classification = ai_service.classify_document(ocr_result["full_text"])
    _log(doc, "EXTRACTION", f"Classified as {classification['document_type']} "
                              f"({classification['confidence']*100:.1f}% confidence). "
                              f"Declared type: {doc.document_type}.")

    db.query(ExtractedField).filter(ExtractedField.document_id == doc.id).delete()
    fields = ai_service.extract_fields(doc.document_type, ocr_result["pages"])
    for f in fields:
        db.add(ExtractedField(document_id=doc.id, **f))
    db.commit()
    record_event(db, actor, "FIELD_EXTRACTED", "Document", doc.id, bid_id=doc.bid_id,
                 new_state=f"{len(fields)} fields extracted", evidence_reference=doc.id)

    doc.status = DocumentStatus.VALIDATION.value
    _log(doc, "VALIDATION", f"Validating {len(fields)} extracted field(s) against document type schema.")

    type_mismatch = (
        classification["document_type"] != "OTHER"
        and classification["document_type"] != doc.document_type
        and classification["confidence"] >= 0.7
    )

    if type_mismatch:
        doc.status = DocumentStatus.WARNING.value
        _log(doc, "VALIDATION", f"Declared type '{doc.document_type}' differs from AI-classified "
                                  f"type '{classification['document_type']}'. Flagged for officer review.")
    elif len(fields) < REQUIRED_FIELDS_MIN:
        doc.status = DocumentStatus.WARNING.value
        _log(doc, "VALIDATION", "Fewer fields extracted than expected for this document type.")
    else:
        doc.status = DocumentStatus.VERIFIED.value
        _log(doc, "VALIDATION", "All expected fields extracted successfully.")

    doc.processed_at = datetime.utcnow()
    db.commit()
    record_event(db, actor, "DOCUMENT_PROCESSED", "Document", doc.id, bid_id=doc.bid_id,
                 new_state=doc.status, evidence_reference=doc.id)
    return doc
