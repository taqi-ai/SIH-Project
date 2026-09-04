"""Government/registry connector abstraction.

Every connector below is a SANDBOX / PROTOTYPE implementation — it never calls a
real government system. Responses are clearly labeled "Sandbox Verification" so
the UI never overstates what was actually checked. Swapping in a live connector
later only requires implementing this same interface against the real API.
"""
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ConnectorResult:
    status: str  # VERIFIED | WARNING | FAILED | UNAVAILABLE
    message: str
    response_payload: dict = field(default_factory=dict)
    latency_ms: int = 0
    source_label: str = "Sandbox Verification"


class GovernmentConnector(ABC):
    code: str = "BASE"
    label: str = "Base Connector"

    @abstractmethod
    def verify(self, facts: dict) -> ConnectorResult:
        ...

    def health_check(self) -> dict:
        return {"code": self.code, "label": self.label, "status": "CONNECTED", "mode": "SANDBOX"}

    def get_evidence(self, result: ConnectorResult) -> dict:
        return {"source": self.label, "mode": "SANDBOX", **result.response_payload}

    def _timed(self, fn):
        start = time.perf_counter()
        out = fn()
        latency = int((time.perf_counter() - start) * 1000) + 120  # simulate realistic network latency floor
        return out, latency
