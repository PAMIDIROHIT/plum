# =====================================================================
# LLM Layer - Gemini Client (Native Google API + Async httpx + Vision)
# =====================================================================

import os
import json
import base64
import asyncio
import httpx
from typing import Dict, Any, Optional

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

# ── Async version ────────────────────────────────────────────────────────────

async def call_gemini_api_async(
    system_prompt: str,
    user_content: str,
    image_bytes: Optional[bytes] = None,
    image_mime: str = "image/jpeg",
) -> Dict[str, Any]:
    """
    Async Gemini extraction call via Native Google AI Studio API.
    Supports optional binary image attachment (Vision mode).
    """
    key = os.getenv("GEMINI_API_KEY", GEMINI_API_KEY)
    if not key:
        raise Exception("GEMINI_API_KEY is missing from environment variables.")

    # Build payload for Google Generative AI REST API
    parts = []
    if image_bytes:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        parts.append({
            "inlineData": {
                "mimeType": image_mime,
                "data": b64
            }
        })
        
    parts.append({
        "text": user_content or "Extract all medical information from this document."
    })

    payload = {
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        },
        "contents": [
            {
                "role": "user",
                "parts": parts
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json"
        }
    }

    # gemini-1.5-flash is deprecated (404). Try 2.5-flash first.
    models = ["gemini-2.5-flash", "gemini-1.5-flash-latest"]

    async with httpx.AsyncClient(timeout=30.0) as client:
        for model in models:
            url = GEMINI_URL.format(model=model, key=key)
            try:
                resp = await client.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["candidates"][0]["content"]["parts"][0]["text"]
                    return json.loads(content)
                else:
                    print(f"Gemini API {model} failed: {resp.text}")
            except (httpx.TimeoutException, json.JSONDecodeError):
                continue
            except Exception as e:
                print(f"Gemini API Error: {e}")
                continue

    raise Exception("All Gemini model variants failed via Google AI Studio.")

# ── Sync wrapper (used by extraction_pipeline.py called from sync fallback) ──

def call_gemini_api(
    system_prompt: str,
    user_content: str,
    image_bytes: Optional[bytes] = None,
    image_mime: str = "image/jpeg",
) -> Dict[str, Any]:
    """
    Sync wrapper around the async Gemini client.
    Runs the async coroutine inside a fresh event loop when called from sync code.
    """
    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
            
        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    asyncio.run,
                    call_gemini_api_async(system_prompt, user_content, image_bytes, image_mime),
                )
                return future.result(timeout=35)
        else:
            return asyncio.run(call_gemini_api_async(system_prompt, user_content, image_bytes, image_mime))
    except Exception as e:
        raise Exception(f"Gemini client communication failed: {str(e)}")
