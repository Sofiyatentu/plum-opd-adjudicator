"""Admin API routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import Claim
from app.schemas.claim_schemas import AdminStatsOut, PolicyTermsOut
from app.rules.policy_loader import get_policy

router = APIRouter(tags=["admin"])


@router.get("/admin/stats", response_model=AdminStatsOut)
async def admin_stats(db: AsyncSession = Depends(get_db)):
    """Get adjudication statistics."""
    total = await db.scalar(select(func.count()).select_from(Claim))
    approved = await db.scalar(select(func.count()).select_from(Claim).where(Claim.decision == "APPROVED"))
    rejected = await db.scalar(select(func.count()).select_from(Claim).where(Claim.decision == "REJECTED"))
    partial = await db.scalar(select(func.count()).select_from(Claim).where(Claim.decision == "PARTIAL"))
    manual = await db.scalar(select(func.count()).select_from(Claim).where(Claim.decision == "MANUAL_REVIEW"))
    total_amt = await db.scalar(select(func.coalesce(func.sum(Claim.approved_amount), 0)).select_from(Claim))
    avg_conf = await db.scalar(select(func.coalesce(func.avg(Claim.confidence_score), 0)).select_from(Claim))

    return AdminStatsOut(
        total_claims=total or 0,
        approved_count=approved or 0,
        rejected_count=rejected or 0,
        partial_count=partial or 0,
        manual_review_count=manual or 0,
        total_approved_amount=float(total_amt or 0),
        average_confidence=float(avg_conf or 0),
    )


@router.get("/admin/policy", response_model=PolicyTermsOut)
async def get_policy_terms():
    """Return the current policy terms."""
    policy = get_policy()
    return PolicyTermsOut(
        policy_id=policy.policy_id,
        policy_name=policy.policy_name,
        effective_date=policy.effective_date,
        policy_holder=policy.raw.get("policy_holder", {}),
        coverage_details=policy.raw.get("coverage_details", {}),
        waiting_periods=policy.raw.get("waiting_periods", {}),
        exclusions=policy.raw.get("exclusions", []),
        claim_requirements=policy.raw.get("claim_requirements", {}),
        network_hospitals=policy.network_hospitals,
        cashless_facilities=policy.raw.get("cashless_facilities", {}),
    )
