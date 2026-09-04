import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


def make_pdf(lines):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    y = 750
    for line in lines:
        c.drawString(50, y, line)
        y -= 20
    c.showPage()
    c.save()
    return buf.getvalue()


def test_login_rejects_bad_password(client):
    resp = client.post("/auth/login", json={"email": "officer@test.gov.in", "password": "wrong"})
    assert resp.status_code == 401


def test_end_to_end_bid_flow(client, auth_headers):
    tender_resp = client.post("/tenders", headers=auth_headers, json={
        "tender_number": "TEST/001", "title": "Test Tender", "closing_date": "2027-01-01T00:00:00",
        "min_turnover": 1000000, "min_years_operation": 2, "min_local_content_pct": 40,
        "requires_oem_authorization": False,
    })
    assert tender_resp.status_code == 200
    tender_id = tender_resp.json()["id"]

    bid_resp = client.post(f"/tenders/{tender_id}/bids", headers=auth_headers, json={
        "bidder": {"company_name": "Test Bidder Pvt Ltd", "pan": "AAFCB4521K"},
        "declared_turnover": 1500000, "declared_local_content_pct": 45,
    })
    assert bid_resp.status_code == 200
    bid_id = bid_resp.json()["id"]

    pdf_bytes = make_pdf(["UDYAM REGISTRATION CERTIFICATE", "Enterprise Name: Test Bidder Pvt Ltd",
                           "Udyam Registration Number: UDYAM-TN-01-1234567", "PAN: AAFCB4521K"])
    upload_resp = client.post(
        f"/bids/{bid_id}/documents",
        headers=auth_headers,
        data={"document_type": "UDYAM_CERTIFICATE"},
        files={"file": ("udyam.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload_resp.status_code == 200
    doc_id = upload_resp.json()["id"]

    process_resp = client.post(f"/documents/{doc_id}/process", headers=auth_headers)
    assert process_resp.status_code == 200
    assert process_resp.json()["status"] in ("VERIFIED", "WARNING")
    assert len(process_resp.json()["extracted_fields"]) > 0

    verify_resp = client.post(f"/bids/{bid_id}/verify", headers=auth_headers)
    assert verify_resp.status_code == 200
    assert verify_resp.json()["risk"]["overall_score"] is not None

    findings_resp = client.get(f"/bids/{bid_id}/findings", headers=auth_headers)
    assert findings_resp.status_code == 200


def test_override_requires_justification(client, auth_headers):
    tender_resp = client.post("/tenders", headers=auth_headers, json={
        "tender_number": "TEST/002", "title": "Test Tender 2", "closing_date": "2027-01-01T00:00:00",
    })
    tender_id = tender_resp.json()["id"]
    bid_resp = client.post(f"/tenders/{tender_id}/bids", headers=auth_headers, json={
        "bidder": {"company_name": "Another Bidder"},
    })
    bid_id = bid_resp.json()["id"]
    client.post(f"/bids/{bid_id}/verify", headers=auth_headers)

    evals = client.get(f"/bids/{bid_id}/compliance", headers=auth_headers).json()["evaluations"]
    eval_id = evals[0]["id"]

    bad = client.post(f"/evaluations/{eval_id}/review", headers=auth_headers, json={"action": "OVERRIDE"})
    assert bad.status_code == 400

    good = client.post(f"/evaluations/{eval_id}/review", headers=auth_headers, json={
        "action": "OVERRIDE", "justification": "Verified manually by officer with supporting evidence.",
    })
    assert good.status_code == 200


def test_final_decision_requires_reason(client, auth_headers):
    tender_resp = client.post("/tenders", headers=auth_headers, json={
        "tender_number": "TEST/003", "title": "Test Tender 3", "closing_date": "2027-01-01T00:00:00",
    })
    tender_id = tender_resp.json()["id"]
    bid_resp = client.post(f"/tenders/{tender_id}/bids", headers=auth_headers, json={
        "bidder": {"company_name": "Third Bidder"},
    })
    bid_id = bid_resp.json()["id"]

    no_reason = client.post(f"/bids/{bid_id}/final-decision", headers=auth_headers, json={
        "decision": "QUALIFIED", "reason": ""
    })
    assert no_reason.status_code == 400

    ok = client.post(f"/bids/{bid_id}/final-decision", headers=auth_headers, json={
        "decision": "QUALIFIED", "reason": "All mandatory requirements verified by officer."
    })
    assert ok.status_code == 200
    assert ok.json()["final_decision"] == "QUALIFIED"

    audit = client.get(f"/bids/{bid_id}/audit", headers=auth_headers).json()
    assert audit["chain_integrity"]["valid"] is True
    assert any(e["action"] == "FINAL_DECISION_RECORDED" for e in audit["events"])
