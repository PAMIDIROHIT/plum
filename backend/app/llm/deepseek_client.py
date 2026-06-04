# =====================================================================
# LLM Layer - DeepSeek R1 Client (Async httpx + Robust JSON parsing)
# =====================================================================

import os
import re
import json
import asyncio
import httpx
from typing import Any

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

_HEADERS = {
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost:3000",
    "X-Title": "Plum Adjudicate",
}


def _auth_headers():
    key = os.getenv("OPENROUTER_API_KEY", OPENROUTER_API_KEY)
    return {**_HEADERS, "Authorization": f"Bearer {key}"}


def _strip_thinking(content: str) -> str:
    """Remove DeepSeek R1 <think>...</think> reasoning traces."""
    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", content)
    cleaned = cleaned.replace("```json", "").replace("```", "")
    return cleaned.strip()


def _safe_json_parse(raw: str) -> Any:
    """
    Attempt to extract valid JSON from LLM output even if surrounded
    by extra prose, markdown, or partial reasoning artifacts.
    """
    # Try direct parse first
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Try finding the outermost JSON object
    match = re.search(r"\{[\s\S]*\}", raw)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise json.JSONDecodeError("No valid JSON found in DeepSeek response", raw, 0)


# ── Async version ────────────────────────────────────────────────────────────

async def call_deepseek_api_async(system_prompt: str, user_content: str) -> str:
    """
    Async DeepSeek R1 adjudication call via OpenRouter.
    Tries free tier first, falls back to paid model on queue overload.
    Returns cleaned raw string (JSON will be parsed by caller).
    """
    models = [
        "meta-llama/llama-3.3-70b-instruct:free"
    ]

    def _payload(model: str):
        return {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.1,
        }

    async with httpx.AsyncClient(timeout=90.0) as client:
        for model in models:
            try:
                resp = await client.post(
                    OPENROUTER_URL,
                    headers=_auth_headers(),
                    json=_payload(model),
                )
                if resp.status_code == 200:
                    content = resp.json()["choices"][0]["message"]["content"]
                    return _strip_thinking(content)
                else:
                    print(f"DeepSeek/LLM Error for {model}: {resp.status_code} - {resp.text}")
            except httpx.TimeoutException as e:
                print(f"DeepSeek/LLM Timeout for {model}: {e}")
                continue
            except Exception as e:
                print(f"DeepSeek/LLM Error for {model}: {e}")
                if 'resp' in locals() and hasattr(resp, 'text'):
                    print(f"Response: {resp.text}")
                continue

    raise Exception("All DeepSeek model variants failed via OpenRouter.")


# ── Sync wrapper ─────────────────────────────────────────────────────────────

def call_deepseek_api(system_prompt: str, user_content: str) -> str:
    """
    Sync wrapper around the async DeepSeek client.
    Compatible with both running and non-running event loops.
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
                    call_deepseek_api_async(system_prompt, user_content),
                )
                return future.result(timeout=65)
        else:
            return asyncio.run(call_deepseek_api_async(system_prompt, user_content))
    except Exception as e:
        raise Exception(f"DeepSeek client communication failed: {str(e)}")


# ── Re-export helpers ─────────────────────────────────────────────────────────

def safe_json_parse(raw: str) -> Any:
    """Public alias — used by adjudication_pipeline.py."""
    return _safe_json_parse(raw)
