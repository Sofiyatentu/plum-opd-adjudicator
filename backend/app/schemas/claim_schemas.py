"""Pydantic schemas for Claim API — matching frontend types.ts contract."""
import uuid
from datetime import date, datetime
from pydantic import BaseModel, Field


# ── Submission ────────────────────────────────────────────

class ClaimSubmitResponse(BaseModel):
    claim_id: str
    status: str


class ClaimInputData(BaseModel):
    """Structured JSON input for claims submitted via API (no file uploads)."""
    member_id: str
    member_name: str
    member_join_date: date | None = None
    treatment_date: date
    claim_amount: float
    hospital: str | None = None
    cashless_request: bool = False
    previous_claims_same_day: int = 0
    documents: dict = Field(default_factory=dict)
    # documents contains: prescription, bill, diagnostic_report, pharmacy_bill keys


# ── Adjudication results ──────────────────────────────────

class AdjudicationStepOut(BaseModel):
    step_number: int
    step_name: str
    passed: bool
    details: dict | None = None
    execution_time_ms: int = 0

    model_config = {"from_attributes": True}


class RejectionReasonOut(BaseModel):
    reason_code: str
    reason_description: str
    category: str

    model_config = {"from_attributes": True}


class FraudFlagOut(BaseModel):
    flag_type: str
    flag_details: str

    model_config = {"from_attributes": True}


class ExtractedDocumentOut(BaseModel):
    document_type: str
    structure_json: dict
    extraction_confidence: float | None = None
    raw_text: str | None = None

    model_config = {"from_attributes": True}


class DocumentInfoOut(BaseModel):
    id: str
    file_name: str
    file_type: str
    document_category: str

    model_config = {"from_attributes": True}


class ClaimDetailOut(BaseModel):
    id: str
    claim_code: str
    member_id: str
    member_code: str
    member_name: str
    treatment_date: date
    submission_date: date
    claim_amount: float
    hospital_name: str | None = None
    is_network: bool = False
    is_cashless: bool = False
    status: str
    decision: str | None = None
    approved_amount: float | None = None
    confidence_score: float | None = None
    notes: str | None = None
    adjudication_steps: list[AdjudicationStepOut] = Field(default_factory=list)
    rejection_reasons: list[RejectionReasonOut] = Field(default_factory=list)
    fraud_flags: list[FraudFlagOut] = Field(default_factory=list)
    extracted_data: list[ExtractedDocumentOut] = Field(default_factory=list)
    documents: list[DocumentInfoOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClaimSummaryOut(BaseModel):
    id: str
    claim_code: str
    member_id: str
    member_code: str
    member_name: str
    treatment_date: date
    claim_amount: float
    approved_amount: float | None = None
    status: str
    decision: str | None = None
    hospital_name: str | None = None
    submission_date: date

    model_config = {"from_attributes": True}


class ClaimsListResponse(BaseModel):
    claims: list[ClaimSummaryOut]
    total: int


# ── Member ────────────────────────────────────────────────

class MemberProfileOut(BaseModel):
    id: str
    member_code: str
    name: str
    date_of_birth: date
    gender: str
    join_date: date
    relationship: str
    is_active: bool
    ytd_claimed: float
    family_floater_used: float

    model_config = {"from_attributes": True}


class MemberSummaryOut(BaseModel):
    member_code: str
    name: str
    ytd_claimed: float
    remaining_annual: float
    remaining_family_floater: float
    is_active: bool


# ── Appeal ────────────────────────────────────────────────

class AppealRequest(BaseModel):
    reason: str


class AppealResponse(BaseModel):
    appeal_id: str
    status: str


# ── Admin ─────────────────────────────────────────────────

class PolicyTermsOut(BaseModel):
    """Returns the full policy_terms.json content."""
    policy_id: str
    policy_name: str
    effective_date: str
    policy_holder: dict
    coverage_details: dict
    waiting_periods: dict
    exclusions: list[str]
    claim_requirements: dict
    network_hospitals: list[str]
    cashless_facilities: dict


class AdminStatsOut(BaseModel):
    total_claims: int
    approved_count: int
    rejected_count: int
    partial_count: int
    manual_review_count: int
    total_approved_amount: float
    average_confidence: float
