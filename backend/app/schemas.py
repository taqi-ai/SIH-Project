from datetime import datetime
from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class TenderCreate(BaseModel):
    tender_number: str
    title: str
    organization: str = "Chennai Petroleum Corporation Limited (CPCL)"
    category: str = "Goods"
    estimated_value: float = 0
    closing_date: datetime
    description: str = ""
    min_turnover: float = 0
    min_years_operation: int = 0
    min_local_content_pct: float = 0
    requires_oem_authorization: bool = False


class BidderCreate(BaseModel):
    company_name: str
    pan: str | None = None
    gstin: str | None = None
    cin: str | None = None
    udyam_number: str | None = None
    address: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    enterprise_type: str | None = None
    incorporation_year: int | None = None


class BidCreate(BaseModel):
    bidder: BidderCreate
    declared_turnover: float | None = None
    declared_local_content_pct: float | None = None


class ReviewCreate(BaseModel):
    finding_id: str | None = None
    requirement_evaluation_id: str | None = None
    action: str
    comment: str | None = None
    justification: str | None = None


class FinalDecisionCreate(BaseModel):
    decision: str
    reason: str


class ProcessResultOut(BaseModel):
    status: str
