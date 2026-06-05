// === Claim Summary (for list view) ===

export interface ClaimSummary {
  id: string;
  claim_code: string;
  member_id: string;
  member_code: string;
  member_name: string;
  treatment_date: string;
  claim_amount: number;
  approved_amount: number | null;
  status: string;
  decision: string | null;
  hospital_name: string | null;
  submission_date: string;
}

export interface ClaimsListResponse {
  claims: ClaimSummary[];
  total: number;
}

// === Claim Detail (full view) ===

export interface AdjudicationStep {
  step_number: number;
  step_name: string;
  passed: boolean;
  details: Record<string, unknown> | null;
  execution_time_ms: number;
}

export interface RejectionReason {
  reason_code: string;
  reason_description: string;
  category: string;
}

export interface FraudFlag {
  flag_type: string;
  flag_details: string;
}

export interface ExtractedDocument {
  document_type: string;
  structure_json: Record<string, unknown>;
  extraction_confidence: number | null;
  raw_text?: string;
}

export interface DocumentInfo {
  id: string;
  file_name: string;
  file_type: string;
  document_category: string;
}

export interface ClaimDetail {
  id: string;
  claim_code: string;
  member_id: string;
  member_code: string;
  member_name: string;
  treatment_date: string;
  submission_date: string;
  claim_amount: number;
  hospital_name: string | null;
  is_network: boolean;
  is_cashless: boolean;
  status: string;
  decision: string | null;
  approved_amount: number | null;
  confidence_score: number | null;
  notes: string | null;
  adjudication_steps: AdjudicationStep[];
  rejection_reasons: RejectionReason[];
  fraud_flags: FraudFlag[];
  extracted_data: ExtractedDocument[];
  documents: DocumentInfo[];
  created_at: string;
  updated_at: string;
}

// === Member ===

export interface MemberProfile {
  id: string;
  member_code: string;
  name: string;
  date_of_birth: string;
  gender: string;
  join_date: string;
  relationship: string;
  is_active: boolean;
  ytd_claimed: number;
  family_floater_used: number;
}
