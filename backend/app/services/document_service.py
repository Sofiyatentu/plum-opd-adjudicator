"""Document service — GPT-4o Vision extraction from images/PDFs.

Accepts uploaded files, converts them to images if needed,
sends to OpenAI GPT-4o for structured data extraction.
"""
import base64
import io
import json
import logging
import os
from pathlib import Path
from typing import Optional

from openai import AsyncOpenAI

from app.config import get_settings
from app.models import ExtractedData

logger = logging.getLogger(__name__)

# Structured extraction prompt for prescriptions
PRESCRIPTION_PROMPT = """You are a medical document data extractor. Analyze this medical prescription/document image and extract the following fields in JSON format:

{
  "doctor_name": "Full name of the doctor",
  "doctor_reg": "Doctor registration number (format: STATE/NUMBER/YEAR)",
  "diagnosis": "Primary diagnosis or condition",
  "medicines_prescribed": ["list", "of", "medicines"],
  "treatment": "Treatment or therapy prescribed (if any)",
  "procedures": ["any", "procedures", "mentioned"],
  "patient_name": "Name of the patient (if visible)",
  "date": "Date on the prescription (if visible)"
}

Rules:
- Return ONLY valid JSON, no other text
- Use null for fields that are not found in the document
- For medicines, include dosage if mentioned
- For doctor_reg, look for registration/license numbers
- Be precise and extract exactly what is written"""

# Structured extraction prompt for bills
BILL_PROMPT = """You are a medical bill data extractor. Analyze this medical bill/invoice image and extract the following fields in JSON format:

{
  "hospital_name": "Name of hospital or clinic",
  "bill_number": "Bill/invoice number",
  "bill_date": "Date on the bill",
  "patient_name": "Patient name",
  "consultation_fee": 0,
  "diagnostic_tests": 0,
  "medicines": 0,
  "therapy_charges": 0,
  "procedure_charges": 0,
  "room_charges": 0,
  "total_amount": 0,
  "items": [{"description": "item name", "amount": 0}]
}

Rules:
- Return ONLY valid JSON, no other text
- Use 0 for amount fields not found in the document
- All amounts should be numeric (no currency symbols)
- Extract individual line items if available
- Be precise with amounts"""

# General document extraction prompt
GENERAL_PROMPT = """You are a medical document analyzer. Analyze this medical document image and extract ALL relevant information in JSON format. Categorize it as either a "prescription" or "bill" and extract appropriate fields.

Return JSON in this format:
{
  "document_type": "prescription" or "bill",
  "extracted_data": { ... relevant fields ... },
  "raw_text": "Full text visible in the document",
  "confidence": 0.0 to 1.0
}

Rules:
- Return ONLY valid JSON, no other text
- Be precise and extract exactly what is written
- Include confidence score based on text clarity"""


def _get_openai_client() -> AsyncOpenAI:
    """Create OpenAI async client."""
    settings = get_settings()
    return AsyncOpenAI(api_key=settings.openai_api_key)


async def _image_to_base64(file_bytes: bytes) -> str:
    """Convert image bytes to base64 string."""
    return base64.b64encode(file_bytes).decode("utf-8")


async def _pdf_to_images(file_bytes: bytes) -> list[bytes]:
    """Convert PDF pages to PNG images using PyMuPDF."""
    try:
        import fitz  # PyMuPDF

        images = []
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        for page_num in range(min(len(doc), 5)):  # Max 5 pages
            page = doc[page_num]
            # Render at 2x resolution for better OCR
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            images.append(pix.tobytes("png"))
        doc.close()
        return images
    except ImportError:
        logger.warning("PyMuPDF not installed, cannot process PDFs")
        return []


async def extract_with_gpt4o(
    file_bytes: bytes,
    file_name: str,
    document_type: str = "auto",
) -> dict:
    """Extract structured data from a document image/PDF using GPT-4o Vision.
    
    Args:
        file_bytes: Raw file bytes
        file_name: Original filename
        document_type: "prescription", "bill", or "auto" for auto-detection
    
    Returns:
        Dict with extracted structured data
    """
    client = _get_openai_client()
    
    # Determine file type and prepare images
    ext = Path(file_name).suffix.lower()
    is_pdf = ext == ".pdf"
    
    if is_pdf:
        image_list = await _pdf_to_images(file_bytes)
        if not image_list:
            return {"error": "Failed to process PDF", "raw_text": ""}
    else:
        image_list = [file_bytes]
    
    # Choose prompt based on document type
    if document_type == "prescription":
        prompt = PRESCRIPTION_PROMPT
    elif document_type == "bill":
        prompt = BILL_PROMPT
    else:
        prompt = GENERAL_PROMPT
    
    all_extracted = []
    
    for i, img_bytes in enumerate(image_list):
        b64 = await _image_to_base64(img_bytes)
        
        # Determine MIME type
        if is_pdf:
            mime = "image/png"
        elif ext in (".jpg", ".jpeg"):
            mime = "image/jpeg"
        elif ext == ".png":
            mime = "image/png"
        elif ext == ".webp":
            mime = "image/webp"
        else:
            mime = "image/jpeg"  # fallback
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime};base64,{b64}",
                                    "detail": "high",
                                },
                            },
                        ],
                    }
                ],
                max_tokens=2000,
                temperature=0.1,
            )
            
            raw_response = response.choices[0].message.content.strip()
            
            # Parse JSON from response (handle markdown code blocks)
            json_str = raw_response
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            
            extracted = json.loads(json_str)
            extracted["_page"] = i + 1
            extracted["_raw_response"] = raw_response
            all_extracted.append(extracted)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT-4o response as JSON: {e}")
            all_extracted.append({
                "error": "JSON parse error",
                "raw_text": raw_response,
                "_page": i + 1,
            })
        except Exception as e:
            logger.error(f"GPT-4o Vision API error: {e}")
            all_extracted.append({
                "error": str(e),
                "_page": i + 1,
            })
    
    # Merge results from multiple pages
    if len(all_extracted) == 1:
        result = all_extracted[0]
    else:
        result = _merge_multi_page(all_extracted)
    
    return result


def _merge_multi_page(pages: list[dict]) -> dict:
    """Merge extracted data from multiple PDF pages."""
    merged = {}
    for page in pages:
        for key, value in page.items():
            if key.startswith("_"):
                continue
            if key not in merged:
                merged[key] = value
            elif isinstance(value, list) and isinstance(merged[key], list):
                merged[key].extend(value)
            elif isinstance(value, (int, float)) and isinstance(merged[key], (int, float)):
                merged[key] = max(merged[key], value)  # Take the larger amount
    
    merged["_pages"] = len(pages)
    return merged


async def save_uploaded_file(
    file_bytes: bytes,
    file_name: str,
    claim_id: str,
) -> str:
    """Save uploaded file to disk and return the path."""
    settings = get_settings()
    upload_dir = Path(settings.upload_dir) / str(claim_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / file_name
    file_path.write_bytes(file_bytes)
    return str(file_path)


async def extract_document_data(
    claim_id,
    document_type: str,
    structure_json: dict,
    db,
    raw_text: str | None = None,
    confidence: float | None = None,
) -> ExtractedData:
    """Store structured document data extracted by GPT-4o Vision.
    
    This persists the structured data extracted from uploaded documents.
    """
    # Clean up internal fields before storing
    clean_data = {k: v for k, v in structure_json.items() if not k.startswith("_")}
    
    ed = ExtractedData(
        claim_id=claim_id,
        document_type=document_type,
        structure_json=clean_data,
        extraction_confidence=confidence or 0.90,
        raw_text=raw_text or structure_json.get("_raw_response", ""),
    )
    db.add(ed)
    await db.flush()
    return ed


async def extract_from_uploaded_files(
    claim_id,
    files: list[tuple[str, bytes, str]],  # [(filename, bytes, doc_type), ...]
    db,
) -> list[ExtractedData]:
    """Extract data from uploaded files using GPT-4o Vision and persist."""
    extracted = []
    
    for file_name, file_bytes, doc_type in files:
        # Save file to disk
        await save_uploaded_file(file_bytes, file_name, str(claim_id))
        
        # Extract with GPT-4o Vision
        logger.info(f"Extracting {doc_type} from {file_name} using GPT-4o Vision...")
        result = await extract_with_gpt4o(file_bytes, file_name, doc_type)
        
        # Determine actual document type if auto-detected
        actual_type = doc_type
        if doc_type == "auto" and "document_type" in result:
            actual_type = result["document_type"]
            if "extracted_data" in result:
                result = result["extracted_data"]
        
        confidence = result.pop("confidence", 0.90) if isinstance(result.get("confidence"), (int, float)) else 0.90
        
        ed = await extract_document_data(
            claim_id=claim_id,
            document_type=actual_type,
            structure_json=result,
            db=db,
            confidence=confidence,
        )
        extracted.append(ed)
    
    return extracted


async def extract_from_structured_input(
    claim_id,
    documents: dict,
    db,
) -> list[ExtractedData]:
    """Extract and persist document data from structured API input (JSON)."""
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
