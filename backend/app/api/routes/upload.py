# =====================================================================
# API Routes - Document File Upload Router
# =====================================================================

import io
import json
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional

from ...document_processing.image_processor import image_file_to_text
from ...document_processing.pdf_processor import pdf_file_to_text
from ...document_processing.ocr_validator import assess_document_quality, validate_document_pair
from ...ai_pipeline.extraction_pipeline import run_extraction_pipeline

router = APIRouter()

SUPPORTED_IMAGES = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
SUPPORTED_DOCS = {".pdf"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def _get_mime(ext: str) -> str:
    """Map file extension to MIME type for Gemini Vision API."""
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".bmp": "image/bmp",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
        ".webp": "image/webp",
        ".pdf": "application/pdf",
    }.get(ext, "image/jpeg")


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    STEP 1 of the AI adjudication pipeline: Document ingestion.

    Accepts PDF or image uploads. The pipeline:
      1. Reads the raw binary file
      2. Runs local text extraction (pytesseract / pdfminer) as baseline text
      3. Passes binary directly to Gemini 2.5 Flash Vision for structured extraction
      4. Returns: extracted_text, gemini_extraction (structured JSON), quality score

    Supported: JPEG, PNG, BMP, TIFF, WebP, PDF
    Max size: 10 MB
    """
    filename = file.filename or "unknown"
    ext = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""

    if ext not in SUPPORTED_IMAGES | SUPPORTED_DOCS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file '{ext}'. Use JPG, PNG, BMP, TIFF, WebP, or PDF."
        )

    # Read raw bytes
    try:
        file_bytes = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(file_bytes)//1024} KB). Max allowed: 10 MB."
        )

    # ── Step A: Local text extraction (baseline for quality assessment) ──────
    try:
        if ext in SUPPORTED_IMAGES:
            local_text = image_file_to_text(file_bytes, filename)
            doc_type = "image"
            image_mime = _get_mime(ext)
        else:
            local_text = pdf_file_to_text(file_bytes, filename)
            doc_type = "pdf"
            image_mime = None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Local text extraction failed: {str(e)}")

    # ── Step B: OCR quality assessment on local-extracted text ───────────────
    quality = assess_document_quality(local_text)

    # ── Step C: Gemini Vision / text extraction (primary AI extraction) ──────
    gemini_extraction = None
    gemini_error = None
    try:
        if ext in SUPPORTED_IMAGES:
            # Pass raw binary to Gemini Vision for maximal accuracy
            gemini_extraction = run_extraction_pipeline(
                documents_text=local_text,
                image_bytes=file_bytes,
                image_mime=image_mime,
            )
        else:
            # PDF: pass extracted text to Gemini text mode
            gemini_extraction = run_extraction_pipeline(documents_text=local_text)
    except Exception as e:
        gemini_error = str(e)
        print(f"Gemini Vision extraction failed for {filename}: {e}")

    # ── Step D: Auto-classify document type ──────────────────────────────────
    text_lower = local_text.lower()
    if gemini_extraction and gemini_extraction.get("document_types"):
        detected_type = gemini_extraction["document_types"][0] if gemini_extraction["document_types"] else "unknown"
    elif any(k in text_lower for k in ["prescription", "rx:", "diagnosis:", "dr.", "medicine"]):
        detected_type = "prescription"
    elif any(k in text_lower for k in ["invoice", "bill", "total:", "amount", "consultation fee"]):
        detected_type = "invoice"
    elif any(k in text_lower for k in ["report", "laboratory", "lab result", "test result"]):
        detected_type = "diagnostic_report"
    else:
        detected_type = "unknown"

    return {
        "filename": filename,
        "content_type": file.content_type or "",
        "doc_type": doc_type,
        "detected_document_type": detected_type,
        "file_size_bytes": len(file_bytes),
        "extracted_text": local_text,               # Raw text for textarea auto-fill
        "gemini_extraction": gemini_extraction,      # Structured AI extraction result
        "gemini_error": gemini_error,                # Non-null only if Gemini failed
        "quality_assessment": quality,
        "status": "extracted" if quality["is_legible"] else "low_quality",
        "warning": (
            "Document quality is low. Manual review recommended."
            if not quality["is_legible"] else None
        ),
    }


@router.post("/upload/validate-pair")
async def validate_document_pair_endpoint(
    prescription: UploadFile = File(...),
    bill: UploadFile = File(...)
):
    """
    Accepts prescription + bill as a pair and cross-validates them for
    date consistency and patient name consistency.
    """
    presc_bytes = await prescription.read()
    bill_bytes = await bill.read()

    presc_ext = ("." + prescription.filename.rsplit(".", 1)[-1].lower())
    bill_ext = ("." + bill.filename.rsplit(".", 1)[-1].lower())

    presc_text = (
        image_file_to_text(presc_bytes, prescription.filename)
        if presc_ext in SUPPORTED_IMAGES
        else pdf_file_to_text(presc_bytes, prescription.filename)
    )
    bill_text = (
        image_file_to_text(bill_bytes, bill.filename)
        if bill_ext in SUPPORTED_IMAGES
        else pdf_file_to_text(bill_bytes, bill.filename)
    )

    presc_quality = assess_document_quality(presc_text)
    bill_quality = assess_document_quality(bill_text)
    cross_validation = validate_document_pair(presc_text, bill_text)

    return {
        "prescription": {
            "filename": prescription.filename,
            "extracted_text": presc_text,
            "quality": presc_quality,
        },
        "bill": {
            "filename": bill.filename,
            "extracted_text": bill_text,
            "quality": bill_quality,
        },
        "cross_validation": cross_validation,
        "overall_valid": (
            presc_quality["is_legible"]
            and bill_quality["is_legible"]
            and cross_validation["date_consistent"]
            and cross_validation["patient_consistent"]
        ),
    }
