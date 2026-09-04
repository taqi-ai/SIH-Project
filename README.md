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

## Deploy (single service, free tier, auto-deploy from GitHub)

The app ships as **one Docker image** containing both the Next.js frontend and the FastAPI backend.
The frontend is the only publicly routed process — it proxies `/api/*` requests server-side to the
backend, which listens on an internal port inside the same container. This means the whole platform
runs as a single web service, which fits the free tier of Render, Railway, or any host that builds
from a `Dockerfile` and forwards `$PORT`.

### Render (what this project is currently deployed on)

1. **[render.com](https://render.com)** → New → Web Service → connect the `taqi-ai/SIH-Project` GitHub repo.
2. **Runtime**: Docker (Render auto-detects the root `Dockerfile`) — leave **Start Command** blank so
   Render uses the Dockerfile's `CMD`.
3. **Environment variables**:
   ```
   SECRET_KEY=your-production-secret-key
   AI_PROVIDER=local
   DATABASE_URL=<leave unset to use SQLite, or add a Render PostgreSQL instance's connection string>
   ```
4. **Add a PostgreSQL database** (optional, free tier available): Render → New → PostgreSQL → copy the
   Internal Database URL into `DATABASE_URL` above.
5. **Deploy**. Every push to `main` auto-builds and redeploys.

### Railway (alternative, same Dockerfile)

1. **[railway.app](https://railway.app)** → New Project → Deploy from GitHub repo → select the repo.
2. Railway auto-detects `railway.json` (`builder: dockerfile`) — no start command override needed.
3. Add the same environment variables as above (`SECRET_KEY`, `AI_PROVIDER`, optional `DATABASE_URL`
   from an added PostgreSQL plugin).
4. Deploy. Push to `main` → Railway auto-rebuilds.

**That's it.** No `NEXT_PUBLIC_API_BASE` to configure — the frontend and backend share one origin.

---

## Design principle
Deterministic checks (dates, thresholds, exact-match IDs, booleans) run in the rule engine, never the AI.
AI handles OCR/extraction, document classification, semantic contradiction detection, and natural-language
findings/recommendations. The AI never renders a qualify/disqualify verdict — only the officer does, via the
Final Decision screen, with a mandatory justification recorded in the audit trail.
