# =====================================================================
# Document Processing - PDF Text Extractor
# =====================================================================

import io
from typing import Optional


def extract_text_from_pdf_bytes(pdf_bytes: bytes, filename: str = "") -> str:
    """
    Extracts text from PDF bytes using available parsing backends.

    Strategy (in order of preference):
    1. pdfminer.six — text-based PDFs (most accurate)
    2. PyPDF2 — fallback reader for simpler PDFs
    3. Graceful error placeholder
    """
    # Strategy 1: pdfminer.six (best for structured text PDFs)
    try:
        from pdfminer.high_level import extract_text_to_fp
        from pdfminer.layout import LAParams

        output = io.StringIO()
        extract_text_to_fp(
            io.BytesIO(pdf_bytes),
            output,
            laparams=LAParams(),
            output_type="text",
            codec="utf-8",
        )
        text = output.getvalue().strip()
        if text:
            return text
    except ImportError:
        pass
    except Exception as e:
        print(f"pdfminer failed for {filename}: {e}")

    # Strategy 2: PyPDF2 fallback
    try:
        import PyPDF2

        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        pages_text = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                pages_text.append(page_text.strip())
        combined = "\n\n".join(pages_text)
        if combined.strip():
            return combined
    except ImportError:
        pass
    except Exception as e:
        print(f"PyPDF2 failed for {filename}: {e}")

    # Strategy 3: Scanned PDF — flag it for vision-based processing
    return (
        f"[SCANNED_PDF: {filename}]\n"
        "This PDF appears to be image-based (scanned). "
        "Manual review or OCR pre-processing required."
    )


def pdf_file_to_text(file_content: bytes, filename: str) -> str:
    """
    Public interface: accepts raw PDF bytes and filename.
    Returns extracted text string.
    """
    if not filename.lower().endswith(".pdf"):
        return f"[NOT_A_PDF: {filename}]"
    return extract_text_from_pdf_bytes(file_content, filename)


def get_pdf_page_count(pdf_bytes: bytes) -> Optional[int]:
    """Returns the number of pages in a PDF, or None if unreadable."""
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        return len(reader.pages)
    except Exception:
        pass
    try:
        from pdfminer.high_level import extract_pages
        count = sum(1 for _ in extract_pages(io.BytesIO(pdf_bytes)))
        return count
    except Exception:
        return None
