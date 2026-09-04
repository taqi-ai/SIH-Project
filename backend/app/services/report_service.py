from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from sqlalchemy.orm import Session
from app.models import Bid, ComplianceEvaluation, ComplianceFinding, OfficerReview, AuditEvent, Verification
from app.config import settings


def generate_bid_report(bid_id: str, db: Session) -> str:
    bid = db.query(Bid).filter(Bid.id == bid_id).first()
    if not bid:
        raise ValueError("Bid not found")

    evaluations = db.query(ComplianceEvaluation).filter(ComplianceEvaluation.bid_id == bid_id).all()
    findings = db.query(ComplianceFinding).filter(ComplianceFinding.bid_id == bid_id).all()
    reviews = db.query(OfficerReview).filter(OfficerReview.bid_id == bid_id).all()
    audit = db.query(AuditEvent).filter(AuditEvent.bid_id == bid_id).order_by(AuditEvent.timestamp).all()
    verifications = db.query(Verification).filter(Verification.bid_id == bid_id).all()

    out_path = settings.reports_dir / f"compliance_report_{bid_id}.pdf"
    doc = SimpleDocTemplate(str(out_path), pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleC", parent=styles["Title"], fontSize=16, spaceAfter=4)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=12, spaceBefore=14, spaceAfter=6, textColor=colors.HexColor("#0f2540"))
    small = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8.5, textColor=colors.HexColor("#555555"))
    body = styles["Normal"]

    story = [
        Paragraph("Bid Compliance Evaluation Report", title_style),
        Paragraph("AI-Powered Integrated Bid Compliance Verification Platform for GeM Procurement", small),
        Paragraph("Ministry of Petroleum &amp; Natural Gas — Chennai Petroleum Corporation Limited (CPCL)", small),
        Spacer(1, 10),
    ]

    story.append(Paragraph("Tender &amp; Bidder Details", h2))
    info_table = Table([
        ["Tender Number", bid.tender.tender_number, "Bid ID", bid.id],
        ["Tender Title", bid.tender.title, "Bidder", bid.bidder.company_name],
        ["Organization", bid.tender.organization, "PAN", bid.bidder.pan or "N/A"],
        ["Closing Date", bid.tender.closing_date.strftime("%d %b %Y"), "GSTIN", bid.bidder.gstin or "N/A"],
    ], colWidths=[85, 165, 70, 150])
    info_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f2f5f8")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f2f5f8")),
    ]))
    story.append(info_table)

    story.append(Paragraph("Compliance Score &amp; Risk", h2))
    story.append(Paragraph(
        f"<b>Compliance Score:</b> {bid.compliance_score or 'N/A'}/100 &nbsp;&nbsp; "
        f"<b>Risk Level:</b> {bid.risk_level or 'N/A'}", body))

    story.append(Paragraph("Requirements Matrix", h2))
    rows = [["Requirement", "Status", "Confidence", "Evidence"]]
    for e in evaluations:
        rows.append([
            e.requirement.label, e.status,
            f"{int((e.confidence or 0) * 100)}%" if e.confidence else "-",
            e.evidence_document_id or "-",
        ])
    req_table = Table(rows, colWidths=[190, 80, 70, 130])
    req_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f2540")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ]))
    story.append(req_table)

    story.append(Paragraph("External Verification Results (Sandbox Connectors)", h2))
    vrows = [["Connector", "Status", "Source"]]
    for v in verifications:
        vrows.append([v.connector_label, v.status, v.source_label])
    vtable = Table(vrows, colWidths=[220, 80, 170])
    vtable.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f2540")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ]))
    story.append(vtable)

    story.append(Paragraph("AI Findings", h2))
    if findings:
        for f in findings:
            story.append(Paragraph(f"<b>{f.title}</b> — Severity: {f.severity}, Status: {f.status}", body))
            story.append(Paragraph(f.description, small))
    else:
        story.append(Paragraph("No AI findings recorded.", body))

    story.append(Paragraph("Officer Reviews &amp; Overrides", h2))
    if reviews:
        for r in reviews:
            story.append(Paragraph(
                f"<b>{r.action}</b> by {r.officer_id} — {r.comment or r.justification or ''}", small))
    else:
        story.append(Paragraph("No officer reviews recorded yet.", body))

    story.append(Paragraph("Final Decision", h2))
    story.append(Paragraph(
        f"<b>{bid.final_decision or 'PENDING'}</b> — entered by Procurement Officer "
        f"({bid.final_decision_by or 'not yet decided'}). "
        f"Reason: {bid.final_decision_reason or 'N/A'}", body))
    story.append(Paragraph(
        "This decision was entered by a human Procurement Officer. The AI system does not "
        "autonomously qualify or disqualify bidders.", small))

    story.append(Paragraph("Audit Trail Summary (SHA-256 hash-chained, tamper-evident)", h2))
    arows = [["Timestamp", "Actor", "Action"]]
    for a in audit[-25:]:
        arows.append([a.timestamp.strftime("%d-%b %H:%M:%S"), a.actor, a.action])
    atable = Table(arows, colWidths=[110, 140, 220])
    atable.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f2540")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ]))
    story.append(atable)

    story.append(Spacer(1, 14))
    story.append(Paragraph(
        f"Generated {datetime.utcnow().strftime('%d %b %Y %H:%M UTC')} · SIH26100 Prototype · "
        "Not a certified legal/regulatory document.", small))

    doc.build(story)
    return str(out_path)
