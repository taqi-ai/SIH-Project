import random
from datetime import datetime

from app.connectors.base import GovernmentConnector, ConnectorResult

# Seeded sandbox debarment registry — mirrors what a real CPCL/GeM debarment
# feed would return. Names deliberately match one seeded demo bidder so the
# "problematic" fixture is genuinely caught by the connector, not hard-coded elsewhere.
DEBARMENT_REGISTRY = {
    "SUNRISE TRADERS PRIVATE LIMITED": {
        "order_ref": "CPCL/VIG/DEB/2024/117",
        "reason": "Debarred for 24 months — supply of non-conforming valve assemblies",
        "valid_from": "2024-01-15", "valid_to": "2026-01-14",
    }
}


def _seeded_rng(seed_str: str) -> random.Random:
    return random.Random(abs(hash(seed_str)) % (10 ** 8))


class UdyamConnector(GovernmentConnector):
    code, label = "UDYAM", "Udyam Registration Portal"

    def verify(self, facts: dict) -> ConnectorResult:
        udyam_no = facts.get("udyam_number")
        if not udyam_no:
            return ConnectorResult("UNAVAILABLE", "No Udyam number extracted from uploaded documents.")
        valid = bool(facts.get("udyam_valid", True))
        payload = {
            "udyam_number": udyam_no,
            "enterprise_type": facts.get("enterprise_type", "Small"),
            "registration_status": "Active" if valid else "Not Found",
        }
        if valid:
            return ConnectorResult("VERIFIED", "Udyam registration confirmed in sandbox registry.", payload)
        return ConnectorResult("FAILED", "Udyam number not found in sandbox registry.", payload)


class GstnConnector(GovernmentConnector):
    code, label = "GSTN", "GST Network (GSTN)"

    def verify(self, facts: dict) -> ConnectorResult:
        gstin = facts.get("gst_gstin")
        if not gstin:
            return ConnectorResult("UNAVAILABLE", "No GSTIN extracted from uploaded documents.")
        active = bool(facts.get("gstin_active", True))
        payload = {
            "gstin": gstin,
            "legal_name": facts.get("company_name"),
            "gstin_status": "Active" if active else "Cancelled",
            "filing_status": "Regular" if active else "Defaulter",
        }
        status = "VERIFIED" if active else "FAILED"
        return ConnectorResult(status, f"GSTIN {'active' if active else 'inactive'} per sandbox GSTN mirror.", payload)


class IncomeTaxConnector(GovernmentConnector):
    code, label = "INCOME_TAX", "Income Tax e-Filing Portal"

    def verify(self, facts: dict) -> ConnectorResult:
        pan = facts.get("bidder_pan")
        if not pan:
            return ConnectorResult("UNAVAILABLE", "No PAN extracted from uploaded documents.")
        payload = {
            "pan": pan,
            "pan_status": "Active" if facts.get("pan_valid", True) else "Inoperative",
            "itr_filed": facts.get("itr_filed", True),
        }
        status = "VERIFIED" if payload["pan_status"] == "Active" and payload["itr_filed"] else "WARNING"
        return ConnectorResult(status, "PAN status checked against sandbox e-filing mirror.", payload)


class EpfoConnector(GovernmentConnector):
    code, label = "EPFO", "EPFO Establishment Registry"

    def verify(self, facts: dict) -> ConnectorResult:
        active = bool(facts.get("epfo_active", True))
        payload = {"establishment_id": facts.get("epfo_number", "N/A"), "status": "Active" if active else "Inactive"}
        return ConnectorResult("VERIFIED" if active else "FAILED", "EPFO establishment status checked (sandbox).", payload)


class EsicConnector(GovernmentConnector):
    code, label = "ESIC", "ESIC Establishment Registry"

    def verify(self, facts: dict) -> ConnectorResult:
        active = bool(facts.get("esic_active", True))
        payload = {"establishment_id": facts.get("esic_number", "N/A"), "status": "Active" if active else "Inactive"}
        return ConnectorResult("VERIFIED" if active else "FAILED", "ESIC establishment status checked (sandbox).", payload)


class StartupIndiaConnector(GovernmentConnector):
    code, label = "STARTUP_INDIA", "Startup India Recognition Registry"

    def verify(self, facts: dict) -> ConnectorResult:
        if not facts.get("is_startup"):
            return ConnectorResult("VERIFIED", "Not applicable — bidder has not claimed Startup India status.", {"applicable": False})
        payload = {"recognition_number": facts.get("startup_recognition_number", "N/A")}
        return ConnectorResult("VERIFIED", "Startup India recognition confirmed (sandbox).", payload)


class NsicConnector(GovernmentConnector):
    code, label = "NSIC", "NSIC Single Point Registration"

    def verify(self, facts: dict) -> ConnectorResult:
        if not facts.get("claims_nsic_exemption"):
            return ConnectorResult("VERIFIED", "Not applicable — bidder has not claimed NSIC exemption.", {"applicable": False})
        payload = {"registration_number": facts.get("nsic_number", "N/A")}
        return ConnectorResult("VERIFIED", "NSIC registration confirmed (sandbox).", payload)


class DigiLockerConnector(GovernmentConnector):
    code, label = "DIGILOCKER", "DigiLocker Document Verification"

    def verify(self, facts: dict) -> ConnectorResult:
        verified = bool(facts.get("digilocker_verified", True))
        payload = {"documents_checked": facts.get("document_count", 0), "issuer_signature_valid": verified}
        return ConnectorResult("VERIFIED" if verified else "WARNING",
                                "Document issuer signatures checked via sandbox DigiLocker mirror.", payload)


class DebarmentConnector(GovernmentConnector):
    code, label = "DEBARMENT", "CPCL / GeM Debarment Registry"

    def verify(self, facts: dict) -> ConnectorResult:
        name = (facts.get("company_name") or "").strip().upper()
        entry = DEBARMENT_REGISTRY.get(name)
        if entry:
            return ConnectorResult("FAILED", "Bidder found on active debarment list.", {"listed": True, **entry})
        return ConnectorResult("VERIFIED", "No active debarment record found (sandbox registry).", {"listed": False})


class MiiConnector(GovernmentConnector):
    code, label = "MII", "Make in India Local Content Registry"

    def verify(self, facts: dict) -> ConnectorResult:
        pct = facts.get("local_content_pct")
        required = facts.get("min_local_content_pct")
        if pct is None:
            return ConnectorResult("UNAVAILABLE", "Local content percentage not extracted from MII declaration.")
        payload = {"declared_pct": pct, "required_pct": required}
        if required is not None and pct < required:
            return ConnectorResult("FAILED", "Declared local content below tender-mandated threshold.", payload)
        if required is not None and (pct - required) < 5:
            return ConnectorResult("WARNING", "Declared local content close to threshold — recommend manual review.", payload)
        return ConnectorResult("VERIFIED", "Local content declaration consistent with MII policy (sandbox).", payload)


CONNECTOR_REGISTRY: dict[str, GovernmentConnector] = {
    c.code: c for c in [
        UdyamConnector(), GstnConnector(), IncomeTaxConnector(), EpfoConnector(), EsicConnector(),
        StartupIndiaConnector(), NsicConnector(), DigiLockerConnector(), DebarmentConnector(), MiiConnector(),
    ]
}
