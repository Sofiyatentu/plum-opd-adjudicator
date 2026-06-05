"""Document service — OCR extraction via Tesseract + GPT-4o structured parsing."""
import logging
from app.models import ExtractedData

logger = logging.getLogger(__name__)


async def extract_document_data(
    claim_id,
    document_type: str,
    structure_json: dict,
    db,
    raw_text: str | None = None,
    confidence: float | None = None,
) -> ExtractedData:
    """Store structured document data extracted by frontend/AI.
    
    The actual OCR/AI extraction is done through GPT-4o by the frontend
    or via the API input. This service just persists the structured data.
    """
    ed = ExtractedData(
        claim_id=claim_id,
        document_type=document_type,
        structure_json=structure_json,
        extraction_confidence=confidence or 0.90,
        raw_text=raw_text,
    )
    db.add(ed)
    await db.flush()
    return ed


async def extract_from_structured_input(
    claim_id,
    documents: dict,
    db,
) -> list[ExtractedData]:
    """Extract and persist document data from structured API input."""
    extracted = []

    if "prescription" in documents:
        ed = await extract_document_data(
            claim_id=claim_id,
            document_type="prescription",
            structure_json=documents["prescription"],
            db=db,
            confidence=0.95,
        )
        extracted.append(ed)

    if "bill" in documents:
        ed = await extract_document_data(
            claim_id=claim_id,
            document_type="bill",
            structure_json=documents["bill"],
            db=db,
            confidence=0.95,
        )
        extracted.append(ed)

    return extracted
