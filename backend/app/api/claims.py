"""Claims API routes."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.claim_schemas import (
    ClaimInputData, ClaimSubmitResponse, ClaimDetailOut, ClaimsListResponse,
    AppealRequest, AppealResponse,
)
from app.services.claim_service import submit_claim_from_json, get_claim_detail, list_claims, appeal_claim

router = APIRouter(tags=["claims"])


@router.post("/claims", response_model=ClaimSubmitResponse)
async def submit_claim(data: dict = Body(...), db: AsyncSession = Depends(get_db)):
    """Submit a new claim with structured JSON data."""
    claim_input = ClaimInputData(**data)
    claim, detail = await submit_claim_from_json(claim_input, db)
    await db.commit()
    return ClaimSubmitResponse(claim_id=str(claim.id), status=claim.status)


@router.get("/claims", response_model=ClaimsListResponse)
async def list_member_claims(member_id: str, db: AsyncSession = Depends(get_db)):
    """List all claims for a member."""
    return await list_claims(member_id, db)


@router.get("/claims/{claim_id}", response_model=ClaimDetailOut)
async def get_claim(claim_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get full claim detail with adjudication results."""
    return await get_claim_detail(claim_id, db)


@router.post("/claims/{claim_id}/appeal", response_model=AppealResponse)
async def file_appeal(claim_id: uuid.UUID, appeal: AppealRequest, db: AsyncSession = Depends(get_db)):
    """File an appeal against a claim decision."""
    result = await appeal_claim(claim_id, appeal.reason, db)
    await db.commit()
    return result
