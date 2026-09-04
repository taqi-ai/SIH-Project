export interface User {
  id: string;
  email: string;
  full_name: string;
  designation: string;
  organization: string;
  role: string;
}

export interface Tender {
  id: string;
  tender_number: string;
  title: string;
  organization: string;
  category: string;
  estimated_value: number;
  published_date: string;
  closing_date: string;
  status: string;
  description: string;
  min_turnover: number;
  min_years_operation: number;
  min_local_content_pct: number;
  requires_oem_authorization: boolean;
  bid_count: number;
  max_risk?: string | null;
  requirements?: Requirement[];
  bids?: Bid[];
}

export interface Requirement {
  id: string;
  code: string;
  label: string;
  document_type: string | null;
  mandatory: boolean;
  rule_definition: Record<string, unknown>;
  applicable: boolean;
}

export interface Bidder {
  id: string;
  company_name: string;
  pan: string | null;
  gstin: string | null;
  cin: string | null;
  udyam_number: string | null;
  address: string | null;
  contact_email: string | null;
  contact_phone: string | null;
  enterprise_type: string | null;
  incorporation_year: number | null;
}

export interface Bid {
  id: string;
  tender_id: string;
  bidder: Bidder;
  status: string;
  submitted_at: string;
  declared_turnover: number | null;
  declared_local_content_pct: number | null;
  compliance_score: number | null;
  risk_level: string | null;
  final_decision: string | null;
  final_decision_reason: string | null;
  final_decision_by: string | null;
  final_decision_at: string | null;
  document_count: number;
  tender?: Tender;
  risk?: RiskAssessment | null;
}

export interface ExtractedField {
  id: string;
  field_name: string;
  field_value: string;
  confidence: number;
  page: number;
  source: string;
  bounding_box: Record<string, number> | null;
}

export interface DocumentRecord {
  id: string;
  bid_id: string;
  document_type: string;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  page_count: number;
  status: string;
  uploaded_at: string;
  processed_at: string | null;
  processing_log: { stage: string; message: string; at: string }[];
  extracted_fields: ExtractedField[];
}

export interface Verification {
  id: string;
  connector_code: string;
  connector_label: string;
  status: string;
  response_payload: Record<string, unknown>;
  source_label: string;
  checked_at: string;
  latency_ms: number;
}

export interface ComplianceEvaluation {
  id: string;
  requirement: Requirement;
  status: string;
  evidence_document_id: string | null;
  confidence: number | null;
  rule_trace: Record<string, unknown>;
  finding_summary: string | null;
  officer_status: string | null;
  evaluated_at: string;
}

export interface RiskAssessment {
  overall_score: number;
  risk_level: string;
  document_completeness_pct: number;
  registry_verification_pct: number;
  tender_compliance_pct: number;
  consistency_pct: number;
  risk_factors: string[];
  computed_at: string;
}

export interface Finding {
  id: string;
  bid_id: string;
  finding_type: string;
  title: string;
  severity: string;
  description: string;
  evidence_document_id: string | null;
  evidence_page: number | null;
  compared_document_id: string | null;
  compared_page: number | null;
  field_a: string | null;
  field_b: string | null;
  value_a: string | null;
  value_b: string | null;
  similarity: number | null;
  confidence: number;
  recommendation: string | null;
  status: string;
  created_at: string;
}

export interface AuditEvent {
  id: string;
  bid_id: string | null;
  tender_id: string | null;
  actor: string;
  action: string;
  entity_type: string;
  entity_id: string | null;
  previous_state: string | null;
  new_state: string | null;
  evidence_reference: string | null;
  timestamp: string;
  prev_hash: string;
  event_hash: string;
}

export interface DashboardSummary {
  active_tenders: number;
  bids_under_review: number;
  compliant_bids: number;
  high_risk_bids: number;
  pending_verification: number;
  documents_processed: number;
  verification_success_rate: number;
  risk_distribution: { LOW: number; MEDIUM: number; HIGH: number };
  recent_tenders: Tender[];
  recent_activity: { actor: string; action: string; entity_type: string; timestamp: string }[];
}

export interface ConnectorStatus {
  code: string;
  label: string;
  status: string;
  mode: string;
  last_checked: string | null;
  last_status: string | null;
  last_response: Record<string, unknown> | null;
  total_checks: number;
}
