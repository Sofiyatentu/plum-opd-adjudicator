"""Members API routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.claim_schemas import MemberSummaryOut
from app.services.member_service import get_member_summary

router = APIRouter(tags=["members"])


@router.get("/members/{member_id}", response_model=MemberSummaryOut)
async def get_member(member_id: str, db: AsyncSession = Depends(get_db)):
    """Get member summary (matches frontend api.ts contract)."""
    member = await get_member_summary(member_id, db)
    if not member:
        # Return a default for unknown members
        from app.rules.policy_loader import get_policy
        policy = get_policy()
        return MemberSummaryOut(
            member_code=member_id,
            name="Unknown Member",
            ytd_claimed=0,
            remaining_annual=policy.annual_limit,
            remaining_family_floater=policy.family_floater_limit,
            is_active=True,
        )
    return member
