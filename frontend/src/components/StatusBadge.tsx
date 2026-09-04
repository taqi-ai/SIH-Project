const MAP: Record<string, { cls: string; label?: string }> = {
  VERIFIED: { cls: "badge-verified" },
  WARNING: { cls: "badge-warning" },
  FAILED: { cls: "badge-failed" },
  PENDING: { cls: "badge-pending" },
  NOT_APPLICABLE: { cls: "badge-na", label: "N/A" },
  UNAVAILABLE: { cls: "badge-pending", label: "UNAVAILABLE" },
  QUEUED: { cls: "badge-pending" },
  PROCESSING: { cls: "badge-pending" },
  OCR: { cls: "badge-pending" },
  EXTRACTION: { cls: "badge-pending" },
  VALIDATION: { cls: "badge-pending" },
  OPEN: { cls: "badge-warning" },
  ACCEPTED: { cls: "badge-verified" },
  REJECTED: { cls: "badge-pending" },
  CLARIFICATION_REQUESTED: { cls: "badge-warning", label: "CLARIFICATION" },
  QUALIFIED: { cls: "badge-verified" },
  DISQUALIFIED: { cls: "badge-failed" },
  CLARIFICATION_REQUIRED: { cls: "badge-warning" },
  CONNECTED: { cls: "badge-verified" },
};

export function StatusBadge({ status }: { status: string }) {
  const entry = MAP[status] || { cls: "badge-pending" };
  return <span className={`badge ${entry.cls}`}>{(entry.label || status).replace(/_/g, " ")}</span>;
}

const RISK_MAP: Record<string, string> = { LOW: "risk-low", MEDIUM: "risk-medium", HIGH: "risk-high" };

export function RiskBadge({ level }: { level: string | null | undefined }) {
  if (!level) return <span className="badge badge-pending">UNSCORED</span>;
  return <span className={`badge ${RISK_MAP[level] || "badge-pending"}`}>{level} RISK</span>;
}

const SEV_MAP: Record<string, string> = {
  LOW: "badge-pending",
  MEDIUM: "badge-warning",
  HIGH: "badge-failed",
  CRITICAL: "badge-failed",
};

export function SeverityBadge({ severity }: { severity: string }) {
  return <span className={`badge ${SEV_MAP[severity] || "badge-pending"}`}>{severity}</span>;
}
