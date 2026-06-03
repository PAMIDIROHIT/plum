# =====================================================================
# LLM Layer - Gemini 2.5 Flash OpenRouter Client
# =====================================================================

import os
import json
import requests
from typing import Dict, Any

# Fetch API Key dynamically from environment variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

def call_gemini_api(system_prompt: str, user_content: str) -> Dict[str, Any]:
    """
    Submits raw medical text inputs to Gemini 2.5 Flash via OpenRouter API.
    Uses fallback model or raises Exception on timeout/network issues.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "Plum Adjudicate"
    }
    
    payload = {
        "model": "google/gemini-2.5-flash",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            res_json = response.json()
            content = res_json["choices"][0]["message"]["content"]
            return json.loads(content)
            
        # Attempt fallback to Gemini 1.5 flash model
        payload["model"] = "google/gemini-flash-1.5"
        fallback_resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=15
        )
        if fallback_resp.status_code == 200:
            res_json = fallback_resp.json()
            content = res_json["choices"][0]["message"]["content"]
            return json.loads(content)
            
        raise Exception(f"OpenRouter Gemini API returned status {response.status_code}")
    except Exception as e:
        raise Exception(f"Gemini client communication failed: {str(e)}")
