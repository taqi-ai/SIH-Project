import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON, Enum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def gen_id(prefix: str):
    return lambda: f"{prefix}-{uuid.uuid4().hex[:10].upper()}"


def now():
    return datetime.utcnow()


# ---------------------------------------------------------------- enums ----

class UserRole(str, enum.Enum):
    PROCUREMENT_OFFICER = "PROCUREMENT_OFFICER"
    ADMIN = "ADMIN"


class TenderStatus(str, enum.Enum):
    OPEN = "OPEN"
    UNDER_EVALUATION = "UNDER_EVALUATION"
    CLOSED = "CLOSED"


class BidStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    DOCUMENTS_PENDING = "DOCUMENTS_PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    EVALUATED = "EVALUATED"
    QUALIFIED = "QUALIFIED"
    DISQUALIFIED = "DISQUALIFIED"
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"


class DocumentType(str, enum.Enum):
    UDYAM_CERTIFICATE = "UDYAM_CERTIFICATE"
    GST_CERTIFICATE = "GST_CERTIFICATE"
    PAN_CARD = "PAN_CARD"
    INCOME_TAX_RETURN = "INCOME_TAX_RETURN"
    MII_DECLARATION = "MII_DECLARATION"
    EPFO_CERTIFICATE = "EPFO_CERTIFICATE"
    ESIC_CERTIFICATE = "ESIC_CERTIFICATE"
    STARTUP_INDIA_CERTIFICATE = "STARTUP_INDIA_CERTIFICATE"
    NSIC_CERTIFICATE = "NSIC_CERTIFICATE"
    OEM_AUTHORIZATION = "OEM_AUTHORIZATION"
    AFFIDAVIT = "AFFIDAVIT"
    FINANCIAL_STATEMENT = "FINANCIAL_STATEMENT"
    TURNOVER_DECLARATION = "TURNOVER_DECLARATION"
    TENDER_SPECIFIC = "TENDER_SPECIFIC"
    OTHER = "OTHER"


class DocumentStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    OCR = "OCR"
    EXTRACTION = "EXTRACTION"
    VALIDATION = "VALIDATION"
    VERIFIED = "VERIFIED"
    WARNING = "WARNING"
    FAILED = "FAILED"


class VerificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    WARNING = "WARNING"
    FAILED = "FAILED"
    UNAVAILABLE = "UNAVAILABLE"


class RequirementStatus(str, enum.Enum):
    VERIFIED = "VERIFIED"
    WARNING = "WARNING"
    FAILED = "FAILED"
    PENDING = "PENDING"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class Severity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ReviewAction(str, enum.Enum):
    ACCEPT_FINDING = "ACCEPT_FINDING"
    REJECT_FINDING = "REJECT_FINDING"
    REQUEST_CLARIFICATION = "REQUEST_CLARIFICATION"
    MARK_VERIFIED = "MARK_VERIFIED"
    MARK_FAILED = "MARK_FAILED"
    ADD_COMMENT = "ADD_COMMENT"
    OVERRIDE = "OVERRIDE"


class FinalDecision(str, enum.Enum):
    QUALIFIED = "QUALIFIED"
    DISQUALIFIED = "DISQUALIFIED"
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"


# --------------------------------------------------------------- models ----

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id("USR"))
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    full_name: Mapped[str] = mapped_column(String)
    designation: Mapped[str] = mapped_column(String, default="Procurement Officer")
    organization: Mapped[str] = mapped_column(String, default="Chennai Petroleum Corporation Limited (CPCL)")
    role: Mapped[str] = mapped_column(String, default=UserRole.PROCUREMENT_OFFICER.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Tender(Base):
    __tablename__ = "tenders"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id("TDR"))
    tender_number: Mapped[str] = mapped_column(String, unique=True)
    title: Mapped[str] = mapped_column(String)
    organization: Mapped[str] = mapped_column(String, default="Chennai Petroleum Corporation Limited (CPCL)")
    category: Mapped[str] = mapped_column(String, default="Goods")
    estimated_value: Mapped[float] = mapped_column(Float, default=0)
    published_date: Mapped[datetime] = mapped_column(DateTime, default=now)
    closing_date: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String, default=TenderStatus.OPEN.value)
    description: Mapped[str] = mapped_column(Text, default="")
    min_turnover: Mapped[float] = mapped_column(Float, default=0)
    min_years_operation: Mapped[int] = mapped_column(Integer, default=0)
    min_local_content_pct: Mapped[float] = mapped_column(Float, default=0)
    requires_oem_authorization: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    requirements: Mapped[list["TenderRequirement"]] = relationship(back_populates="tender", cascade="all, delete-orphan")
    bids: Mapped[list["Bid"]] = relationship(back_populates="tender", cascade="all, delete-orphan")


class TenderRequirement(Base):
    __tablename__ = "tender_requirements"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id("REQ"))
    tender_id: Mapped[str] = mapped_column(String, ForeignKey("tenders.id"))
    code: Mapped[str] = mapped_column(String)  # e.g. UDYAM, GST, PAN, MII, EPFO...
    label: Mapped[str] = mapped_column(String)
    document_type: Mapped[str] = mapped_column(String, nullable=True)
    mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    rule_definition: Mapped[dict] = mapped_column(JSON, default=dict)  # data-driven rule
    applicable: Mapped[bool] = mapped_column(Boolean, default=True)

    tender: Mapped["Tender"] = relationship(back_populates="requirements")


class Bidder(Base):
    __tablename__ = "bidders"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id("BDR"))
    company_name: Mapped[str] = mapped_column(String)
    pan: Mapped[str] = mapped_column(String, nullable=True)
    gstin: Mapped[str] = mapped_column(String, nullable=True)
    cin: Mapped[str] = mapped_column(String, nullable=True)
    udyam_number: Mapped[str] = mapped_column(String, nullable=True)
    address: Mapped[str] = mapped_column(String, nullable=True)
    contact_email: Mapped[str] = mapped_column(String, nullable=True)
    contact_phone: Mapped[str] = mapped_column(String, nullable=True)
    enterprise_type: Mapped[str] = mapped_column(String, nullable=True)  # Micro/Small/Medium
    incorporation_year: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Bid(Base):
    __tablename__ = "bids"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id("BID"))
    tender_id: Mapped[str] = mapped_column(String, ForeignKey("tenders.id"))
    bidder_id: Mapped[str] = mapped_column(String, ForeignKey("bidders.id"))
    status: Mapped[str] = mapped_column(String, default=BidStatus.SUBMITTED.value)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    declared_turnover: Mapped[float] = mapped_column(Float, nullable=True)
    declared_local_content_pct: Mapped[float] = mapped_column(Float, nullable=True)
    compliance_score: Mapped[float] = mapped_column(Float, nullable=True)
    risk_level: Mapped[str] = mapped_column(String, nullable=True)
    final_decision: Mapped[str] = mapped_column(String, nullable=True)
    final_decision_reason: Mapped[str] = mapped_column(Text, nullable=True)
    final_decision_by: Mapped[str] = mapped_column(String, nullable=True)
    final_decision_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    demo_profile: Mapped[str] = mapped_column(String, nullable=True)  # COMPLIANT|MEDIUM|PROBLEMATIC (seed marker only)

    tender: Mapped["Tender"] = relationship(back_populates="bids")
    bidder: Mapped["Bidder"] = relationship()
    documents: Mapped[list["Document"]] = relationship(back_populates="bid", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id("DOC"))
    bid_id: Mapped[str] = mapped_column(String, ForeignKey("bids.id"))
    document_type: Mapped[str] = mapped_column(String)
    original_filename: Mapped[str] = mapped_column(String)
    stored_path: Mapped[str] = mapped_column(String)
    mime_type: Mapped[str] = mapped_column(String)
    size_bytes: Mapped[int] = mapped_column(Integer)
    page_count: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String, default=DocumentStatus.QUEUED.value)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    processed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    ocr_text: Mapped[str] = mapped_column(Text, nullable=True)
    processing_log: Mapped[list] = mapped_column(JSON, default=list)

    bid: Mapped["Bid"] = relationship(back_populates="documents")
    extracted_fields: Mapped[list["ExtractedField"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class ExtractedField(Base):
    __tablename__ = "extracted_fields"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id("FLD"))
    document_id: Mapped[str] = mapped_column(String, ForeignKey("documents.id"))
    field_name: Mapped[str] = mapped_column(String)
    field_value: Mapped[str] = mapped_column(String)
    confidence: Mapped[float] = mapped_column(Float, default=0.9)
    page: Mapped[int] = mapped_column(Integer, default=1)
    source: Mapped[str] = mapped_column(String, default="AI_EXTRACTION")
    bounding_box: Mapped[dict] = mapped_column(JSON, nullable=True)  # {x,y,w,h} normalized, optional

    document: Mapped["Document"] = relationship(back_populates="extracted_fields")


class Verification(Base):
    __tablename__ = "verifications"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id("VER"))
    bid_id: Mapped[str] = mapped_column(String, ForeignKey("bids.id"))
    connector_code: Mapped[str] = mapped_column(String)  # UDYAM, GSTN, INCOME_TAX, EPFO, ESIC, STARTUP_INDIA, NSIC, DIGILOCKER, DEBARMENT, MII
    connector_label: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default=VerificationStatus.PENDING.value)
    request_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    response_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    source_label: Mapped[str] = mapped_column(String, default="Sandbox Verification")
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)


class ComplianceEvaluation(Base):
    __tablename__ = "compliance_evaluations"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id("EVL"))
    bid_id: Mapped[str] = mapped_column(String, ForeignKey("bids.id"))
    requirement_id: Mapped[str] = mapped_column(String, ForeignKey("tender_requirements.id"))
    status: Mapped[str] = mapped_column(String, default=RequirementStatus.PENDING.value)
    evidence_document_id: Mapped[str] = mapped_column(String, ForeignKey("documents.id"), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=True)
    rule_trace: Mapped[dict] = mapped_column(JSON, default=dict)  # deterministic rule evaluation trace
    finding_summary: Mapped[str] = mapped_column(String, nullable=True)
    officer_status: Mapped[str] = mapped_column(String, nullable=True)  # officer override of status
    evaluated_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    requirement: Mapped["TenderRequirement"] = relationship()


class ComplianceFinding(Base):
    __tablename__ = "compliance_findings"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id("FND"))
    bid_id: Mapped[str] = mapped_column(String, ForeignKey("bids.id"))
    finding_type: Mapped[str] = mapped_column(String)  # CONTRADICTION | MISSING_INFO | RULE_VIOLATION | ANOMALY
    title: Mapped[str] = mapped_column(String)
    severity: Mapped[str] = mapped_column(String, default=Severity.MEDIUM.value)
    description: Mapped[str] = mapped_column(Text)
    evidence_document_id: Mapped[str] = mapped_column(String, ForeignKey("documents.id"), nullable=True)
    evidence_page: Mapped[int] = mapped_column(Integer, nullable=True)
    compared_document_id: Mapped[str] = mapped_column(String, ForeignKey("documents.id"), nullable=True)
    compared_page: Mapped[int] = mapped_column(Integer, nullable=True)
    field_a: Mapped[str] = mapped_column(String, nullable=True)
    field_b: Mapped[str] = mapped_column(String, nullable=True)
    value_a: Mapped[str] = mapped_column(String, nullable=True)
    value_b: Mapped[str] = mapped_column(String, nullable=True)
    similarity: Mapped[float] = mapped_column(Float, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.9)
    recommendation: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="OPEN")  # OPEN | ACCEPTED | REJECTED | CLARIFICATION_REQUESTED
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id("RSK"))
    bid_id: Mapped[str] = mapped_column(String, ForeignKey("bids.id"))
    overall_score: Mapped[float] = mapped_column(Float)
    risk_level: Mapped[str] = mapped_column(String)
    document_completeness_pct: Mapped[float] = mapped_column(Float)
    registry_verification_pct: Mapped[float] = mapped_column(Float)
    tender_compliance_pct: Mapped[float] = mapped_column(Float)
    consistency_pct: Mapped[float] = mapped_column(Float)
    risk_factors: Mapped[list] = mapped_column(JSON, default=list)
    computed_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class OfficerReview(Base):
    __tablename__ = "officer_reviews"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id("REV"))
    bid_id: Mapped[str] = mapped_column(String, ForeignKey("bids.id"))
    finding_id: Mapped[str] = mapped_column(String, ForeignKey("compliance_findings.id"), nullable=True)
    requirement_evaluation_id: Mapped[str] = mapped_column(String, ForeignKey("compliance_evaluations.id"), nullable=True)
    officer_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String)
    comment: Mapped[str] = mapped_column(Text, nullable=True)
    justification: Mapped[str] = mapped_column(Text, nullable=True)  # mandatory when action == OVERRIDE
    previous_state: Mapped[str] = mapped_column(String, nullable=True)
    new_state: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id("AUD"))
    bid_id: Mapped[str] = mapped_column(String, ForeignKey("bids.id"), nullable=True)
    tender_id: Mapped[str] = mapped_column(String, ForeignKey("tenders.id"), nullable=True)
    actor: Mapped[str] = mapped_column(String)  # user email or "SYSTEM_AI" / "SYSTEM_RULES_ENGINE"
    action: Mapped[str] = mapped_column(String)
    entity_type: Mapped[str] = mapped_column(String)
    entity_id: Mapped[str] = mapped_column(String, nullable=True)
    previous_state: Mapped[str] = mapped_column(Text, nullable=True)
    new_state: Mapped[str] = mapped_column(Text, nullable=True)
    evidence_reference: Mapped[str] = mapped_column(String, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=now)
    prev_hash: Mapped[str] = mapped_column(String, default="0" * 64)
    event_hash: Mapped[str] = mapped_column(String)
