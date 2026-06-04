# =====================================================================
# Document Processing - Image Text Extractor
# =====================================================================

import base64
import io
import re
from typing import Optional


def extract_text_from_image_bytes(image_bytes: bytes, filename: str = "") -> str:
    """
    Extracts text from image bytes using available OCR backends.
    
    Strategy (in order of preference):
    1. pytesseract (if installed) — offline OCR
    2. easyocr (if installed) — offline OCR fallback
    3. Base64 encode and pass to Gemini Vision via API
    4. Graceful fallback with an error message for the LLM to handle
    """
    # Strategy 1: Try pytesseract
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes))
        img_gray = img.convert("L")
        text = pytesseract.image_to_string(img_gray, lang="eng")
        if text.strip():
            return text.strip()
    except Exception as e:
        pass

    # Strategy 2: Try EasyOCR (Skip on Render to prevent 512MB RAM OOM crash)
    import os
    if not os.getenv("RENDER"):
        try:
            import easyocr
            import numpy as np
            from PIL import Image
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            img_np = np.array(img)
            # Suppress verbose output by disabling logging or wrapping
            reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            result = reader.readtext(img_np, detail=0)
            text = "\n".join(result)
            if text.strip():
                return text.strip()
        except Exception as e:
            print(f"EasyOCR failed for {filename}: {e}")
    else:
        print("Skipping EasyOCR on Render to prevent memory OOM. Falling back to Gemini.")

    # Strategy 3: Return base64 placeholder that Gemini Vision can process
    try:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
        mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
        return f"[IMAGE_BASE64:{mime}:{b64[:100]}...]"
    except Exception:
        pass

    return f"[UNREADABLE_IMAGE: {filename}]"


def image_file_to_text(file_content: bytes, filename: str) -> str:
    """
    Public interface: accepts raw file bytes and filename.
    Returns extracted text or a structured placeholder.
    """
    supported = (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp")
    if not any(filename.lower().endswith(ext) for ext in supported):
        return f"[UNSUPPORTED_IMAGE_FORMAT: {filename}]"

    return extract_text_from_image_bytes(file_content, filename)


def encode_image_for_vision_api(image_bytes: bytes, filename: str) -> dict:
    """
    Encodes an image for use with Gemini Vision / OpenRouter vision API calls.
    Returns a message-content-part dict compatible with the OpenAI vision format.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
    mime_map = {
        "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "png": "image/png", "gif": "image/gif",
        "webp": "image/webp", "bmp": "image/bmp",
    }
    mime = mime_map.get(ext, "image/jpeg")
    b64_data = base64.b64encode(image_bytes).decode("utf-8")
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{mime};base64,{b64_data}"}
    }
