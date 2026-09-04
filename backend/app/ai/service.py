"""Pluggable AI service abstraction.

Everything here does semantic/interpretive work that cannot be reduced to a
plain comparison: document classification, field extraction from raw OCR text,
cross-document contradiction detection, and natural-language finding/recommendation
generation. All deterministic checks (dates, thresholds, exact-match IDs, booleans)
live in app/rules/engine.py instead — that separation is intentional.

Current provider: LOCAL (regex/heuristic extraction — no external API, no key
required). Swap by implementing the same method surface against an LLM provider
and pointing AI_PROVIDER at it; nothing else in the codebase needs to change.
"""
import re
import difflib

CLASSIFY_KEYWORDS = {
    "UDYAM_CERTIFICATE": ["udyam registration", "udyam number"],
    "GST_CERTIFICATE": ["goods and services tax", "gstin", "certificate of registration"],
    "PAN_CARD": ["permanent account number", "income tax department"],
    "INCOME_TAX_RETURN": ["income tax return", "assessment year", "acknowledgement number"],
    "MII_DECLARATION": ["make in india", "local content"],
    "EPFO_CERTIFICATE": ["employees' provident fund", "epfo", "establishment id"],
    "ESIC_CERTIFICATE": ["employees' state insurance", "esic"],
    "STARTUP_INDIA_CERTIFICATE": ["startup india", "recognition number"],
    "NSIC_CERTIFICATE": ["nsic", "single point registration"],
    "OEM_AUTHORIZATION": ["authorized dealer", "oem", "authorization letter"],
    "FINANCIAL_STATEMENT": ["audited financial statement", "balance sheet"],
    "TURNOVER_DECLARATION": ["turnover declaration", "annual turnover"],
    "TENDER_SPECIFIC": ["undertaking", "affidavit", "years in operation"],
}

# label -> canonical field name, per document type
EXTRACTION_LABELS: dict[str, list[tuple[str, str]]] = {
    "UDYAM_CERTIFICATE": [
        (r"Enterprise Name:\s*(.+)", "company_name"),
        (r"Udyam Registration Number:\s*([A-Z0-9-]+)", "udyam_number"),
        (r"Date of Registration:\s*([\d/-]+)", "registration_date"),
        (r"Enterprise Category:\s*(\w+)", "enterprise_type"),
        (r"PAN:\s*([A-Z0-9]+)", "bidder_pan"),
    ],
    "GST_CERTIFICATE": [
        (r"Legal Name:\s*(.+)", "company_name"),
        (r"GSTIN:\s*([A-Z0-9]+)", "gst_gstin"),
        (r"Valid Upto:\s*([\d/-]+)", "gst_valid_upto"),
    ],
    "PAN_CARD": [
        (r"Name of PAN Holder:\s*(.+)", "company_name"),
        (r"Permanent Account Number:\s*([A-Z0-9]+)", "bidder_pan"),
    ],
    "INCOME_TAX_RETURN": [
        (r"PAN:\s*([A-Z0-9]+)", "bidder_pan"),
        (r"Assessment Year:\s*([\d-]+)", "assessment_year"),
        (r"Gross Turnover \(Rs\.\):\s*([\d,]+)", "declared_turnover"),
    ],
    "MII_DECLARATION": [
        (r"Local Content Percentage:\s*([\d.]+)", "local_content_pct"),
    ],
    "EPFO_CERTIFICATE": [
        (r"Establishment ID:\s*(\S+)", "epfo_number"),
        (r"Status:\s*(\w+)", "epfo_status_raw"),
    ],
    "ESIC_CERTIFICATE": [
        (r"Establishment ID:\s*(\S+)", "esic_number"),
        (r"Status:\s*(\w+)", "esic_status_raw"),
    ],
    "STARTUP_INDIA_CERTIFICATE": [
        (r"Recognition Number:\s*(\S+)", "startup_recognition_number"),
    ],
    "NSIC_CERTIFICATE": [
        (r"NSIC Registration Number:\s*(\S+)", "nsic_number"),
    ],
    "OEM_AUTHORIZATION": [
        (r"OEM Name:\s*(.+)", "oem_name"),
        (r"Authorized Dealer/Distributor:\s*(.+)", "company_name"),
    ],
    "FINANCIAL_STATEMENT": [
        (r"Financial Year:\s*(\S+)", "financial_year"),
        (r"Turnover \(Rs\.\):\s*([\d,]+)", "declared_turnover"),
    ],
    "TURNOVER_DECLARATION": [
        (r"Financial Year:\s*(\S+)", "financial_year"),
        (r"Turnover \(Rs\.\):\s*([\d,]+)", "declared_turnover"),
    ],
    "TENDER_SPECIFIC": [
        (r"Years in Operation:\s*(\d+)", "years_in_operation"),
    ],
}


class AIService:
    provider = "local"

    def classify_document(self, text: str) -> dict:
        lowered = text.lower()
        best_type, best_score = "OTHER", 0
        for doc_type, keywords in CLASSIFY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in lowered)
            if score > best_score:
                best_type, best_score = doc_type, score
        confidence = min(0.99, 0.55 + best_score * 0.18) if best_score else 0.3
        return {"document_type": best_type, "confidence": round(confidence, 3)}

    def extract_fields(self, document_type: str, pages: list[str]) -> list[dict]:
        patterns = EXTRACTION_LABELS.get(document_type, [])
        results = []
        for page_no, page_text in enumerate(pages, start=1):
            for pattern, field_name in patterns:
                m = re.search(pattern, page_text, re.IGNORECASE)
                if m:
                    value = m.group(1).strip()
                    confidence = 0.97 if len(value) > 2 else 0.75
                    results.append({
                        "field_name": field_name, "field_value": value,
                        "confidence": confidence, "page": page_no, "source": "AI_EXTRACTION",
                    })
        return results

    def semantic_similarity(self, a: str, b: str) -> float:
        return round(difflib.SequenceMatcher(None, (a or "").lower(), (b or "").lower()).ratio(), 3)

    def detect_contradictions(self, fields_by_document: list[dict]) -> list[dict]:
        """fields_by_document: [{document_id, document_type, filename, fields: {name: value}}]"""
        findings = []
        findings.extend(self._detect_numeric_contradictions(fields_by_document))
        compare_fields = ["company_name", "bidder_pan"]
        for field_name in compare_fields:
            occurrences = [
                (d, d["fields"].get(field_name))
                for d in fields_by_document if d["fields"].get(field_name)
            ]
            for i in range(len(occurrences)):
                for j in range(i + 1, len(occurrences)):
                    doc_a, val_a = occurrences[i]
                    doc_b, val_b = occurrences[j]
                    sim = self.semantic_similarity(val_a, val_b)
                    exact = val_a.strip().upper().replace(" ", "").replace(".", "") == \
                            val_b.strip().upper().replace(" ", "").replace(".", "")
                    if not exact and sim < 0.98:
                        severity = "HIGH" if field_name == "bidder_pan" else ("MEDIUM" if sim > 0.85 else "HIGH")
                        classification = (
                            "Potential naming variation / review recommended" if sim > 0.85
                            else "Significant discrepancy — manual verification recommended"
                        )
                        findings.append({
                            "finding_type": "CONTRADICTION",
                            "title": f"{field_name.replace('_', ' ').title()} mismatch across documents",
                            "severity": severity,
                            "description": (
                                f"'{val_a}' (in {doc_a['filename']}) does not exactly match "
                                f"'{val_b}' (in {doc_b['filename']}). Semantic similarity: {int(sim*100)}%. "
                                f"{classification}"
                            ),
                            "evidence_document_id": doc_a["document_id"],
                            "compared_document_id": doc_b["document_id"],
                            "field_a": field_name, "field_b": field_name,
                            "value_a": val_a, "value_b": val_b,
                            "similarity": sim,
                            "confidence": round(0.8 + (1 - sim) * 0.15, 3),
                            "recommendation": "Procurement Officer should review the discrepancy and request "
                                               "clarification if it cannot be reconciled from other evidence.",
                        })
        return findings

    def _detect_numeric_contradictions(self, fields_by_document: list[dict]) -> list[dict]:
        findings = []
        occurrences = []
        for d in fields_by_document:
            raw = d["fields"].get("declared_turnover")
            if raw is None:
                continue
            try:
                value = float(str(raw).replace(",", ""))
            except ValueError:
                continue
            occurrences.append((d, value))
        for i in range(len(occurrences)):
            for j in range(i + 1, len(occurrences)):
                doc_a, val_a = occurrences[i]
                doc_b, val_b = occurrences[j]
                if val_a == 0:
                    continue
                pct_diff = abs(val_a - val_b) / val_a
                if pct_diff > 0.03:
                    findings.append({
                        "finding_type": "CONTRADICTION",
                        "title": "Potential turnover inconsistency",
                        "severity": "MEDIUM" if pct_diff < 0.25 else "HIGH",
                        "description": (
                            f"Declared turnover in {doc_a['filename']} (Rs. {val_a:,.0f}) differs from "
                            f"{doc_b['filename']} (Rs. {val_b:,.0f}) by {pct_diff*100:.1f}%."
                        ),
                        "evidence_document_id": doc_a["document_id"],
                        "compared_document_id": doc_b["document_id"],
                        "field_a": "declared_turnover", "field_b": "declared_turnover",
                        "value_a": f"{val_a:,.0f}", "value_b": f"{val_b:,.0f}",
                        "similarity": round(1 - pct_diff, 3),
                        "confidence": round(min(0.98, 0.7 + pct_diff), 3),
                        "recommendation": "Procurement Officer should review the discrepancy between the "
                                           "declared turnover figures before relying on either value.",
                    })
        return findings

    def generate_recommendation(self, finding_title: str, severity: str) -> str:
        if severity in ("HIGH", "CRITICAL"):
            return f"Recommend Procurement Officer review before qualification: {finding_title.lower()} requires resolution."
        return f"Recommend Procurement Officer note this during evaluation: {finding_title.lower()}."


ai_service = AIService()
