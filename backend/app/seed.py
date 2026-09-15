"""Seeds realistic SIH26100 demo data: 1 procurement officer, 3 tenders, 3 bidders
each (compliant / medium-risk / problematic), generated PDF documents run through
the full pipeline (OCR -> extraction -> verification -> compliance -> risk) so the
dashboard and every screen show real, derived numbers on first login.

Run: python -m app.seed
"""
import io
from datetime import datetime, timedelta

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from app.database import Base, engine, SessionLocal
from app.models import User, Tender, TenderRequirement, Bidder, Bid, Document
from app.security import hash_password
from app.rules.requirements_catalog import DEFAULT_REQUIREMENTS
from app.storage import storage
from app.services.document_pipeline import process_document
from app.services.compliance_service import evaluate_bid
from app.audit_chain import record_event

NOW = datetime.utcnow()


def make_pdf_bytes(heading_lines: list[str], label_lines: list[str]) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    y = height - 60
    c.setFont("Helvetica-Bold", 13)
    for line in heading_lines:
        c.drawString(50, y, line)
        y -= 20
    y -= 10
    c.setFont("Helvetica", 10)
    for line in label_lines:
        c.drawString(50, y, line)
        y -= 18
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(50, 45, "Prototype demo document generated for SIH26100 — not a real government certificate.")
    c.showPage()
    c.save()
    return buf.getvalue()


def add_document(db, bid, document_type, filename, heading, labels):
    content = make_pdf_bytes(heading, labels)
    rel_path = storage.save(bid.id, filename, content)
    doc = Document(
        bid_id=bid.id, document_type=document_type, original_filename=filename,
        stored_path=rel_path, mime_type="application/pdf", size_bytes=len(content), status="QUEUED",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def build_docs_for_bidder(db, bid, profile: dict):
    """profile carries every value used to fill document templates for one bidder."""
    docs = []
    docs.append(add_document(
        db, bid, "UDYAM_CERTIFICATE", "udyam_certificate.pdf",
        ["UDYAM REGISTRATION CERTIFICATE", "Ministry of Micro, Small and Medium Enterprises, Government of India"],
        [f"Enterprise Name: {profile['udyam_name']}", f"Udyam Registration Number: {profile['udyam_number']}",
         f"Date of Registration: {profile['udyam_date']}", f"Enterprise Category: {profile['enterprise_type']}",
         f"PAN: {profile['pan']}"],
    ))
    docs.append(add_document(
        db, bid, "GST_CERTIFICATE", "gst_certificate.pdf",
        ["CERTIFICATE OF REGISTRATION", "Goods and Services Tax Network (GSTN)"],
        [f"Legal Name: {profile['gst_name']}", f"GSTIN: {profile['gstin']}", f"Valid Upto: {profile['gst_valid_upto']}"],
    ))
    docs.append(add_document(
        db, bid, "PAN_CARD", "pan_card.pdf",
        ["INCOME TAX DEPARTMENT", "GOVT. OF INDIA — Permanent Account Number Card"],
        [f"Name of PAN Holder: {profile['pan_name']}", f"Permanent Account Number: {profile['pan']}"],
    ))
    docs.append(add_document(
        db, bid, "INCOME_TAX_RETURN", "income_tax_return.pdf",
        ["INCOME TAX RETURN — ACKNOWLEDGEMENT", "Income Tax Department, Government of India"],
        [f"PAN: {profile['pan']}", f"Assessment Year: {profile['assessment_year']}",
         f"Gross Turnover (Rs.): {profile['itr_turnover']}"],
    ))
    docs.append(add_document(
        db, bid, "FINANCIAL_STATEMENT", "audited_financial_statement.pdf",
        ["AUDITED FINANCIAL STATEMENT", "Statutory Auditor's Report — Annexure B (Turnover)"],
        [f"Financial Year: {profile['financial_year']}", f"Turnover (Rs.): {profile['audited_turnover']}"],
    ))
    docs.append(add_document(
        db, bid, "MII_DECLARATION", "mii_local_content_declaration.pdf",
        ["SELF-DECLARATION", "Public Procurement (Preference to Make in India), Order — Local Content"],
        [f"Local Content Percentage: {profile['local_content_pct']}"],
    ))
    docs.append(add_document(
        db, bid, "EPFO_CERTIFICATE", "epfo_registration.pdf",
        ["EMPLOYEES' PROVIDENT FUND ORGANISATION (EPFO)", "Establishment Registration Certificate"],
        [f"Establishment ID: {profile['epfo_number']}", f"Status: {profile['epfo_status']}"],
    ))
    docs.append(add_document(
        db, bid, "ESIC_CERTIFICATE", "esic_registration.pdf",
        ["EMPLOYEES' STATE INSURANCE CORPORATION (ESIC)", "Establishment Registration Certificate"],
        [f"Establishment ID: {profile['esic_number']}", f"Status: {profile['esic_status']}"],
    ))
    if profile.get("oem_name"):
        docs.append(add_document(
            db, bid, "OEM_AUTHORIZATION", "oem_authorization_letter.pdf",
            ["AUTHORIZATION LETTER", "Original Equipment Manufacturer — Dealer Authorization"],
            [f"OEM Name: {profile['oem_name']}", f"Authorized Dealer/Distributor: {profile['pan_name']}"],
        ))
    docs.append(add_document(
        db, bid, "TENDER_SPECIFIC", "undertaking_affidavit.pdf",
        ["UNDERTAKING / AFFIDAVIT", "Tender-Specific Declaration by Bidder"],
        [f"Years in Operation: {profile['years_in_operation']}"],
    ))
    return docs


def run_pipeline_for_bid(db, bid, actor):
    docs = db.query(Document).filter(Document.bid_id == bid.id).all()
    for d in docs:
        process_document(d.id, db, actor=actor)
    evaluate_bid(bid.id, db, actor=actor)


def seed():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    officer = User(
        email="procurement@cpcl.gov.in", hashed_password=hash_password("demo123"),
        full_name="Arvind Krishnan", designation="Deputy Manager (Procurement)",
        organization="Chennai Petroleum Corporation Limited (CPCL)", role="PROCUREMENT_OFFICER",
    )
    admin = User(
        email="admin@cpcl.gov.in", hashed_password=hash_password("demo123"),
        full_name="System Administrator", designation="Platform Administrator",
        organization="Chennai Petroleum Corporation Limited (CPCL)", role="ADMIN",
    )
    db.add_all([officer, admin])
    db.commit()

    tenders_spec = [
        dict(
            tender_number="CPCL/GEM/2026/PUMP/017", title="Supply of Centrifugal Pumps for CDU-3 Revamp Project",
            category="Goods", estimated_value=48000000, closing_days=18,
            description="Procurement of API-610 compliant centrifugal pumps and spares for the CDU-3 revamp unit at Manali Refinery.",
            min_turnover=50000000, min_years_operation=3, min_local_content_pct=50, requires_oem_authorization=True,
        ),
        dict(
            tender_number="CPCL/GEM/2026/VALVE/044", title="Annual Rate Contract for Industrial Valves & Fittings",
            category="Goods", estimated_value=26000000, closing_days=25,
            description="Rate contract for supply of gate, globe and control valves conforming to ASME/ANSI standards.",
            min_turnover=20000000, min_years_operation=2, min_local_content_pct=40, requires_oem_authorization=True,
        ),
        dict(
            tender_number="CPCL/GEM/2026/FIRE/009", title="Supply & Installation of Fire Safety Systems",
            category="Works", estimated_value=32000000, closing_days=30,
            description="Design, supply, installation, testing and commissioning of fire hydrant and foam suppression systems.",
            min_turnover=30000000, min_years_operation=5, min_local_content_pct=60, requires_oem_authorization=False,
        ),
        dict(
            tender_number="CPCL/GEM/2026/INST/052", title="Supply of DCS Field Instrumentation & Control Systems",
            category="Goods", estimated_value=41000000, closing_days=22,
            description="Procurement of pressure/flow/level transmitters, control valves and DCS integration hardware for the Hydrocracker Unit upgrade.",
            min_turnover=35000000, min_years_operation=4, min_local_content_pct=45, requires_oem_authorization=True,
        ),
        dict(
            tender_number="CPCL/GEM/2026/CIVIL/061", title="Rate Contract for Structural Steel & Piping Materials",
            category="Goods", estimated_value=19500000, closing_days=15,
            description="Annual rate contract for structural steel sections, corrosion-resistant piping and fittings for refinery maintenance works.",
            min_turnover=15000000, min_years_operation=3, min_local_content_pct=55, requires_oem_authorization=False,
        ),
    ]

    tenders = []
    for spec in tenders_spec:
        days = spec.pop("closing_days")
        t = Tender(**spec, closing_date=NOW + timedelta(days=days))
        db.add(t)
        db.commit()
        db.refresh(t)
        for r in DEFAULT_REQUIREMENTS:
            oem_required = spec_get_oem(spec)
            req = TenderRequirement(
                tender_id=t.id, code=r["code"], label=r["label"], document_type=r["document_type"],
                mandatory=r["mandatory"] if r["code"] != "OEM" else oem_required,
                applicable=True if r["code"] != "OEM" else oem_required,
                rule_definition=r["rule_definition"],
            )
            db.add(req)
        db.commit()
        record_event(db, "SYSTEM_SEED", "TENDER_CREATED", "Tender", t.id, tender_id=t.id, new_state=t.title)
        tenders.append(t)

    close_str = lambda t: t.closing_date.strftime("%d/%m/%Y")

    profiles = [
        # ---- COMPLIANT ----
        lambda t: dict(
            profile="COMPLIANT", company="Bharat Precision Engineering Private Limited",
            pan="AAFCB4521K", gstin="33AAFCB4521K1Z5",
            udyam="UDYAM-TN-03-0041827", enterprise_type="Small",
            gst_valid=(t.closing_date + timedelta(days=365)).strftime("%d/%m/%Y"),
            itr_turnover=f"{int(t.min_turnover*1.6):,}", audited_turnover=f"{int(t.min_turnover*1.6):,}",
            local_content=min(95, t.min_local_content_pct + 22), epfo="Active", esic="Active",
            oem="Kirloskar Brothers Limited" if t.requires_oem_authorization else None,
            years=9, incorporation_year=2016,
        ),
        # ---- MEDIUM RISK ----
        lambda t: dict(
            profile="MEDIUM", company="Coastal Industrial Suppliers LLP",
            pan="AAJFC7734M", gstin="33AAJFC7734M1Z2",
            udyam="UDYAM-TN-07-0098213", enterprise_type="Medium",
            gst_valid=(t.closing_date + timedelta(days=20)).strftime("%d/%m/%Y"),
            itr_turnover=f"{int(t.min_turnover*1.04):,}", audited_turnover=f"{int(t.min_turnover*0.97):,}",
            local_content=t.min_local_content_pct + 2, epfo="Active", esic="Active",
            oem="Fluidtech Valves Corp" if t.requires_oem_authorization else None,
            years=4, incorporation_year=2021,
        ),
        # ---- PROBLEMATIC ----
        lambda t: dict(
            profile="PROBLEMATIC", company="Sunrise Traders Private Limited",
            pan="AACFS1122P", gstin="33AACFS9988P1Z9",  # GSTIN-embedded PAN deliberately mismatched
            udyam="UDYAM-TN-11-0075519", enterprise_type="Small",
            gst_valid=(t.closing_date - timedelta(days=40)).strftime("%d/%m/%Y"),  # expired before close
            itr_turnover=f"{int(t.min_turnover*0.7):,}", audited_turnover=f"{int(t.min_turnover*0.52):,}",
            local_content=max(5, t.min_local_content_pct - 18), epfo="Inactive", esic="Active",
            oem=None,  # missing mandatory OEM authorization
            years=2, incorporation_year=2023,
            company_variant="Sunrise Traders Pvt. Ltd.",  # name mismatch across documents
        ),
    ]

    for t in tenders:
        for make_profile in profiles:
            p = make_profile(t)
            bidder = Bidder(
                company_name=p["company"], pan=p["pan"], gstin=p["gstin"], udyam_number=p["udyam"],
                address="SIDCO Industrial Estate, Chennai, Tamil Nadu", contact_email="contact@example.com",
                contact_phone="+91-9800000000", enterprise_type=p["enterprise_type"],
                incorporation_year=p["incorporation_year"],
            )
            db.add(bidder)
            db.commit()
            db.refresh(bidder)

            bid = Bid(
                tender_id=t.id, bidder_id=bidder.id, status="DOCUMENTS_PENDING",
                declared_turnover=float(p["itr_turnover"].replace(",", "")),
                declared_local_content_pct=float(p["local_content"]),
                demo_profile=p["profile"],
            )
            db.add(bid)
            db.commit()
            db.refresh(bid)
            record_event(db, "SYSTEM_SEED", "BID_CREATED", "Bid", bid.id, bid_id=bid.id, tender_id=t.id,
                         new_state=bidder.company_name)

            doc_profile = dict(
                udyam_name=p["company"], udyam_number=p["udyam"], udyam_date="12/04/2021",
                enterprise_type=p["enterprise_type"], pan=p["pan"],
                gst_name=p.get("company_variant", p["company"]), gstin=p["gstin"], gst_valid_upto=p["gst_valid"],
                pan_name=p["company"], assessment_year="2025-26", itr_turnover=p["itr_turnover"],
                financial_year="2024-25", audited_turnover=p["audited_turnover"],
                local_content_pct=p["local_content"], epfo_number=f"TN/CHN/{bidder.id[-6:]}", epfo_status=p["epfo"],
                esic_number=f"ESIC/{bidder.id[-6:]}", esic_status=p["esic"], oem_name=p["oem"],
                years_in_operation=p["years"],
            )
            build_docs_for_bidder(db, bid, doc_profile)
            run_pipeline_for_bid(db, bid, actor="SYSTEM_SEED")

    db.close()
    print("Seed complete.")
    print("Login: procurement@cpcl.gov.in / demo123")


def spec_get_oem(spec):
    return spec.get("requires_oem_authorization", False)


if __name__ == "__main__":
    seed()
