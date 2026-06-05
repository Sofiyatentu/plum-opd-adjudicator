"""Adjudication service — orchestrates engine with DB persistence."""
import time
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.rules.adjudication_engine import AdjudicationEngine
from app.rules.policy_loader import get_policy
from app.models import Claim, AdjudicationStep, RejectionReason, FraudFlag

logger = logging.getLogger(__name__)


async def run_adjudication(claim: Claim, db: AsyncSession) -> None:
    """Run the full 6-step adjudication on a claim and persist results."""
    engine = AdjudicationEngine()

    # Build the structured claim_data dict from the claim + extracted data
    claim_data = _build_claim_data(claim)

    t_start = time.perf_counter()
    result = engine.adjudicate(claim_data)
    total_ms = int((time.perf_counter() - t_start) * 1000)

    # Persist each step
    for step in result.steps:
        db.add(AdjudicationStep(
            claim_id=claim.id,
            step_number=step.step_number,
            step_name=step.step_name,
            passed=step.passed,
            details=step.details,
            execution_time_ms=step.execution_time_ms,
        ))

    # Persist rejection reasons
    for r in result.rejection_reasons:
        db.add(RejectionReason(
            claim_id=claim.id,
            reason_code=r["reason_code"],
            reason_description=r["reason_description"],
            category=r["category"],
        ))

    # Persist fraud flags
    for f in result.fraud_flags:
        db.add(FraudFlag(
            claim_id=claim.id,
            flag_type=f["flag_type"],
            flag_details=f["flag_details"],
        ))

    # Update claim with results
    claim.status = "completed"
    claim.decision = result.decision
    claim.approved_amount = result.approved_amount
    claim.confidence_score = result.confidence_score
    claim.notes = result.notes
    claim.processing_time_ms = total_ms

    await db.flush()
    logger.info(f"Claim {claim.claim_code} adjudicated: {result.decision} (confidence: {result.confidence_score})")


def _build_claim_data(claim: Claim) -> dict:
    """Build claim_data dict from ORM claim + extracted data for engine input."""
    data: dict = {
        "claim_amount": float(claim.claim_amount),
        "treatment_date": str(claim.treatment_date) if claim.treatment_date else None,
        "hospital": claim.hospital_name or "",
        "cashless_request": claim.is_cashless,
        "is_network": claim.is_network,
    }

    # Merge extracted data
    for ed in claim.extracted_data:
        if ed.document_type == "prescription" and ed.structure_json:
            if "documents" not in data:
                data["documents"] = {}
            data["documents"]["prescription"] = ed.structure_json
            # Extract diagnosis and member info
            data["diagnosis"] = ed.structure_json.get("diagnosis", "")
            data["member_name"] = ed.structure_json.get("patient_name", "")
        elif ed.document_type == "bill" and ed.structure_json:
            if "documents" not in data:
                data["documents"] = {}
            data["documents"]["bill"] = ed.structure_json

    # Fallback: if no extracted data, try from claim itself
    if "documents" not in data:
        data["documents"] = {}

    # Member info from claim
    if claim.member:
        data["member_id"] = str(claim.member.member_code)
        data["member_name"] = claim.member.name
        data["member_join_date"] = str(claim.member.join_date) if claim.member.join_date else None

    return data
