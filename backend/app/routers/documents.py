from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse

from app.database import get_db
from app.models import Bid, Document, User, DocumentType
from app.security import get_current_user
from app.serializers import s_document
from app.storage import storage
from app.services.document_pipeline import process_document
from app.audit_chain import record_event
from app.config import settings

router = APIRouter(tags=["documents"])


@router.post("/bids/{bid_id}/documents")
async def upload_document(
    bid_id: str, document_type: str = Form(...), file: UploadFile = File(...),
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    bid = db.query(Bid).filter(Bid.id == bid_id).first()
    if not bid:
        raise HTTPException(404, "Bid not found")
    if document_type not in DocumentType.__members__:
        raise HTTPException(400, f"Unsupported document type: {document_type}")
    if file.content_type not in settings.allowed_mime_types:
        raise HTTPException(400, f"Unsupported file type: {file.content_type}. Only PDF/PNG/JPEG allowed.")

    content = await file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(400, f"File exceeds {settings.max_upload_mb}MB limit")
    if not content:
        raise HTTPException(400, "Empty file")

    relative_path = storage.save(bid_id, file.filename, content)
    doc = Document(
        bid_id=bid_id, document_type=document_type, original_filename=file.filename,
        stored_path=relative_path, mime_type=file.content_type, size_bytes=len(content),
        status="QUEUED",
    )
    db.add(doc)
    if bid.status == "DOCUMENTS_PENDING":
        bid.status = "UNDER_REVIEW"
    db.commit()
    db.refresh(doc)
    record_event(db, user.email, "DOCUMENT_UPLOADED", "Document", doc.id, bid_id=bid_id, evidence_reference=doc.id,
                 new_state=doc.original_filename)
    return s_document(doc)


@router.post("/documents/{document_id}/process")
def process_document_endpoint(document_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = process_document(document_id, db, actor=user.email)
    return s_document(doc)


@router.get("/documents/{document_id}")
def get_document(document_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    return s_document(doc)


@router.get("/documents/{document_id}/file")
def get_document_file(document_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    path = storage.full_path(doc.stored_path)
    if not path.exists():
        raise HTTPException(404, "File missing from storage")
    return FileResponse(str(path), media_type=doc.mime_type, filename=doc.original_filename)


@router.get("/bids/{bid_id}/documents")
def list_bid_documents(bid_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    docs = db.query(Document).filter(Document.bid_id == bid_id).order_by(Document.uploaded_at).all()
    return [s_document(d) for d in docs]
