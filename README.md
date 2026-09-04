# AI-Powered Integrated Bid Compliance Verification Platform for GeM Procurement

SIH26100 prototype — Ministry of Petroleum & Natural Gas / Chennai Petroleum Corporation Limited (CPCL).

Human-in-the-loop platform: AI extracts, verifies, and analyzes bidder compliance documents;
the **Procurement Officer always makes the final qualification decision**.

## Stack
- **Backend**: FastAPI + SQLAlchemy + SQLite (swap `DATABASE_URL` for Postgres — schema is portable)
- **Frontend**: Next.js 14 (App Router) + TypeScript + Tailwind CSS
- **Rules**: deterministic, data-driven rule engine (`backend/app/rules`)
- **AI**: pluggable local extraction/classification/contradiction-detection service (`backend/app/ai`)
- **Connectors**: sandbox government/registry connectors behind a common interface (`backend/app/connectors`) — clearly labeled "Sandbox Verification", swappable for real APIs later
- **Audit**: SHA-256 hash-chained, tamper-evident audit trail (`backend/app/audit_chain`)

## Run it

### Backend
```bash
cd backend
python -m venv venv
./venv/Scripts/pip install -r requirements.txt   # (venv/bin/pip on macOS/Linux)
./venv/Scripts/python -m app.seed                # seeds 3 tenders, 9 bidders, ~85 documents, full pipeline
./venv/Scripts/python -m uvicorn app.main:app --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:3000 — login with `procurement@cpcl.gov.in` / `demo123`.

### Tests
```bash
cd backend
./venv/Scripts/python -m pytest tests/ -q
```

## Golden demo path
Login → Dashboard → Tenders → Tender Detail → Bidder (Bid) Detail →
Documents (upload/process) → Compliance Matrix → Evidence Viewer → Findings →
Officer Review/Override → Final Decision → Audit Trail → Export Report.

Three pre-seeded bidders per tender demonstrate the three demo profiles:
- **Bharat Precision Engineering Pvt Ltd** — fully compliant, LOW risk
- **Coastal Industrial Suppliers LLP** — MEDIUM risk (borderline turnover/local-content, turnover inconsistency)
- **Sunrise Traders Private Limited** — HIGH risk / problematic (expired GST, PAN mismatch, missing OEM authorization, active debarment listing, turnover inconsistency)

## Design principle
Deterministic checks (dates, thresholds, exact-match IDs, booleans) run in the rule engine, never the AI.
AI handles OCR/extraction, document classification, semantic contradiction detection, and natural-language
findings/recommendations. The AI never renders a qualify/disqualify verdict — only the officer does, via the
Final Decision screen, with a mandatory justification recorded in the audit trail.
