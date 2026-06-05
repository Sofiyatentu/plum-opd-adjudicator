"""Member service — CRUD for members."""
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Member
from app.schemas.claim_schemas import MemberProfileOut, MemberSummaryOut
from app.rules.policy_loader import get_policy

logger = logging.getLogger(__name__)


async def get_member_profile(member_code: str, db: AsyncSession) -> MemberProfileOut | None:
    result = await db.execute(
        select(Member).where(Member.member_code == member_code)
    )
    member = result.scalar_one_or_none()
    if not member:
        return None

    return MemberProfileOut(
        id=str(member.id),
        member_code=member.member_code,
        name=member.name,
        date_of_birth=member.date_of_birth,
        gender=member.gender,
        join_date=member.join_date,
        relationship=member.relationship.value if hasattr(member.relationship, 'value') else str(member.relationship),
        is_active=member.is_active,
        ytd_claimed=member.ytd_claimed,
        family_floater_used=member.family_floater_used,
    )


async def get_member_summary(member_code: str, db: AsyncSession) -> MemberSummaryOut | None:
    result = await db.execute(
        select(Member).where(Member.member_code == member_code)
    )
    member = result.scalar_one_or_none()
    if not member:
        return None

    policy = get_policy()
    remaining_annual = policy.annual_limit - member.ytd_claimed
    remaining_family = policy.family_floater_limit - member.family_floater_used

    return MemberSummaryOut(
        member_code=member.member_code,
        name=member.name,
        ytd_claimed=member.ytd_claimed,
        remaining_annual=max(0, remaining_annual),
        remaining_family_floater=max(0, remaining_family),
        is_active=member.is_active,
    )
