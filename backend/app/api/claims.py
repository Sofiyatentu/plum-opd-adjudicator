"""Claims API routes — supports both JSON and file upload submissions."""
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, Body, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.claim_schemas import (
    ClaimInputData, ClaimSubmitResponse, ClaimDetailOut, ClaimsListResponse,
    AppealRequest, AppealResponse,
)
from app.services.claim_service import (
    submit_claim_from_json,
    submit_claim_with_files,
    get_claim_detail,
    list_claims,
    appeal_claim,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["claims"])


@router.post("/claims", response_model=ClaimSubmitResponse)
async def submit_claim(data: dict = Body(...), db: AsyncSession = Depends(get_db)):
    """Submit a new claim with structured JSON data."""
    claim_input = ClaimInputData(**data)
    claim, detail = await submit_claim_from_json(claim_input, db)
    await db.commit()
    return ClaimSubmitResponse(claim_id=str(claim.id), status=claim.status)


@router.post("/claims/upload", response_model=ClaimSubmitResponse)
async def submit_claim_with_upload(
    member_id: str = Form(...),
    member_name: str = Form(...),
    treatment_date: str = Form(...),
    claim_amount: float = Form(...),
    hospital: str = Form(""),
    cashless_request: bool = Form(False),
    prescription_file: UploadFile | None = File(None),
    bill_file: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
):
    """Submit a claim with uploaded document files (images/PDFs).
    
    Files are processed using GPT-4o Vision for data extraction.
    Accepts prescription and/or bill documents as images or PDFs.
    """
    # Collect uploaded files
    files = []
    if prescription_file and prescription_file.filename:
        content = await prescription_file.read()
        if content:
            files.append((prescription_file.filename, content, "prescription"))
            logger.info(f"Received prescription file: {prescription_file.filename} ({len(content)} bytes)")
    
    if bill_file and bill_file.filename:
        content = await bill_file.read()
        if content:
            files.append((bill_file.filename, content, "bill"))
            logger.info(f"Received bill file: {bill_file.filename} ({len(content)} bytes)")
    
    if not files:
        raise HTTPException(
            status_code=400,
            detail="At least one document file (prescription or bill) is required"
        )
    
    # Build claim input data
    claim_data = ClaimInputData(
        member_id=member_id,
        member_name=member_name,
        treatment_date=treatment_date,
        claim_amount=claim_amount,
        hospital=hospital,
        cashless_request=cashless_request,
        documents={},
    )
    
    claim = await submit_claim_with_files(claim_data, files, db)
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
