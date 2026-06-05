"""Claim service — CRUD for claims, submission, and retrieval."""
import uuid
import logging
from datetime import date, datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Claim, Member, ExtractedData, AdjudicationStep, RejectionReason, FraudFlag, Document, Appeal
from app.services.document_service import extract_from_structured_input, extract_from_uploaded_files
from app.services.adjudication_service import run_adjudication
from app.schemas.claim_schemas import ClaimInputData, ClaimDetailOut, ClaimSummaryOut, ClaimsListResponse, AppealResponse
from app.utils.validators import is_network_hospital
from app.rules.policy_loader import get_policy

logger = logging.getLogger(__name__)

def _next_claim_code() -> str:
    return f"CLM_{uuid.uuid4().hex[:8].upper()}"


async def submit_claim_from_json(data: ClaimInputData, db: AsyncSession) -> tuple[Claim, ClaimDetailOut]:
    """Submit a claim from structured JSON input, extract docs, and adjudicate."""
    policy = get_policy()

    # Find or create member
    member = await _get_or_create_member(data, db)

    # Check network hospital
    is_network = is_network_hospital(data.hospital, policy.network_hospitals) if data.hospital else False

    claim = Claim(
        id=uuid.uuid4(),
        claim_code=_next_claim_code(),
        member_id=member.id,
        treatment_date=data.treatment_date,
        submission_date=date.today(),
        claim_amount=data.claim_amount,
        hospital_name=data.hospital or "Self-reported",
        is_network=is_network,
        is_cashless=bool(data.cashless_request and is_network),
        status="processing",
    )
    db.add(claim)
    await db.flush()

    # Extract document data from structured input
    await extract_from_structured_input(
        claim_id=claim.id,
        documents=data.documents,
        db=db,
    )
    await db.flush()

    # Refresh claim with relationships loaded
    await db.refresh(claim, attribute_names=["extracted_data", "member"])

    # Inject extracted data into the claim's in-memory dict for adjudication
    claim.member = member
    # Adjudicate
    await run_adjudication(claim, db)
    await db.flush()

    # Reload with all relationships
    claim_out = await _load_claim_detail(claim.id, db)
    return claim, claim_out


async def submit_claim_with_files(
    data: ClaimInputData,
    files: list[tuple[str, bytes, str]],
    db: AsyncSession,
) -> Claim:
    """Submit a claim with uploaded document files.
    
    Files are processed with GPT-4o Vision for data extraction,
    then the standard adjudication pipeline runs.
    """
    policy = get_policy()

    # Find or create member
    member = await _get_or_create_member(data, db)

    # Check network hospital
    is_network = is_network_hospital(data.hospital, policy.network_hospitals) if data.hospital else False

    claim = Claim(
        id=uuid.uuid4(),
        claim_code=_next_claim_code(),
        member_id=member.id,
        treatment_date=data.treatment_date,
        submission_date=date.today(),
        claim_amount=data.claim_amount,
        hospital_name=data.hospital or "Self-reported",
        is_network=is_network,
        is_cashless=bool(data.cashless_request and is_network),
        status="processing",
    )
    db.add(claim)
    await db.flush()

    # Store Document records for each uploaded file
    for file_name, file_bytes, doc_type in files:
        ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else "unknown"
        doc = Document(
            id=uuid.uuid4(),
            claim_id=claim.id,
            file_name=file_name,
            file_type=ext,
            document_category=doc_type,
            storage_path=f"uploads/{claim.id}/{file_name}",
            file_size_bytes=len(file_bytes),
        )
        db.add(doc)

    await db.flush()

    # Extract document data using GPT-4o Vision
    logger.info(f"Processing {len(files)} document(s) with GPT-4o Vision for claim {claim.claim_code}...")
    await extract_from_uploaded_files(
        claim_id=claim.id,
        files=files,
        db=db,
    )
    await db.flush()

    # Refresh claim with relationships loaded
    await db.refresh(claim, attribute_names=["extracted_data", "member"])
    claim.member = member

    # Run adjudication
    logger.info(f"Running adjudication for claim {claim.claim_code}...")
    await run_adjudication(claim, db)
    await db.flush()

    logger.info(f"Claim {claim.claim_code} complete: {claim.decision} (approved: {claim.approved_amount})")
    return claim



async def _get_or_create_member(data: ClaimInputData, db: AsyncSession) -> Member:
    """Find existing member or create one for testing."""
    result = await db.execute(
        select(Member).where(Member.member_code == data.member_id)
    )
    member = result.scalar_one_or_none()

    if member:
        return member

    # Create new member for test scenarios
    member = Member(
        id=uuid.uuid4(),
        member_code=data.member_id,
        name=data.member_name,
        date_of_birth=date(1985, 1, 1),  # default
        gender="M",
        join_date=data.member_join_date or date(2024, 1, 1),
        relationship="employee",
        is_active=True,
        ytd_claimed=0.0,
        family_floater_used=0.0,
    )
    db.add(member)
    await db.flush()
    return member


async def _load_claim_detail(claim_id: uuid.UUID, db: AsyncSession) -> ClaimDetailOut:
    """Load claim with all relationships and convert to output schema."""
    result = await db.execute(
        select(Claim)
        .where(Claim.id == claim_id)
        .options(
            selectinload(Claim.member),
            selectinload(Claim.documents),
            selectinload(Claim.extracted_data),
            selectinload(Claim.adjudication_steps),
            selectinload(Claim.rejection_reasons),
            selectinload(Claim.fraud_flags),
        )
    )
    claim = result.scalar_one()

    return ClaimDetailOut(
        id=str(claim.id),
        claim_code=claim.claim_code,
        member_id=str(claim.member_id),
        member_code=claim.member.member_code if claim.member else "",
        member_name=claim.member.name if claim.member else "",
        treatment_date=claim.treatment_date,
        submission_date=claim.submission_date,
        claim_amount=claim.claim_amount,
        hospital_name=claim.hospital_name,
        is_network=claim.is_network,
        is_cashless=claim.is_cashless,
        status=claim.status,
        decision=claim.decision,
        approved_amount=claim.approved_amount,
        confidence_score=claim.confidence_score,
        notes=claim.notes,
        adjudication_steps=[
            {"step_number": s.step_number, "step_name": s.step_name, "passed": s.passed, "details": s.details, "execution_time_ms": s.execution_time_ms}
            for s in (claim.adjudication_steps or [])
        ],
        rejection_reasons=[
            {"reason_code": r.reason_code, "reason_description": r.reason_description, "category": r.category}
            for r in (claim.rejection_reasons or [])
        ],
        fraud_flags=[
            {"flag_type": f.flag_type, "flag_details": f.flag_details}
            for f in (claim.fraud_flags or [])
        ],
        extracted_data=[
            {"document_type": e.document_type, "structure_json": e.structure_json or {}, "extraction_confidence": e.extraction_confidence, "raw_text": e.raw_text}
            for e in (claim.extracted_data or [])
        ],
        documents=[
            {"id": str(d.id), "file_name": d.file_name, "file_type": d.file_type, "document_category": d.document_category}
            for d in (claim.documents or [])
        ],
        created_at=claim.created_at or datetime.now(timezone.utc),
        updated_at=claim.updated_at or datetime.now(timezone.utc),
    )


async def get_claim_detail(claim_id: uuid.UUID, db: AsyncSession) -> ClaimDetailOut:
    return await _load_claim_detail(claim_id, db)


async def list_claims(member_id: str, db: AsyncSession) -> ClaimsListResponse:
    result = await db.execute(
        select(Claim, Member)
        .join(Member, Claim.member_id == Member.id)
        .where(Member.member_code == member_id)
        .order_by(Claim.created_at.desc())
    )
    rows = result.all()
    summaries = [
        ClaimSummaryOut(
            id=str(c.id),
            claim_code=c.claim_code,
            member_id=str(c.member_id),
            member_code=m.member_code,
            member_name=m.name,
            treatment_date=c.treatment_date,
            claim_amount=c.claim_amount,
            approved_amount=c.approved_amount,
            status=c.status,
            decision=c.decision,
            hospital_name=c.hospital_name,
            submission_date=c.submission_date,
        )
        for c, m in rows
    ]
    return ClaimsListResponse(claims=summaries, total=len(summaries))


async def appeal_claim(claim_id: uuid.UUID, reason: str, db: AsyncSession) -> AppealResponse:
    appeal = Appeal(
        id=uuid.uuid4(),
        claim_id=claim_id,
        appeal_code=f"APL_{_next_appeal_code()}",
        reason=reason,
        status="pending",
    )
    db.add(appeal)
    await db.flush()
    return AppealResponse(appeal_id=str(appeal.id), status=appeal.status)


def _next_appeal_code() -> str:
    return f"APL_{uuid.uuid4().hex[:8].upper()}"
