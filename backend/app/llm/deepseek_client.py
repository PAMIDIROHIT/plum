# =====================================================================
# LLM Layer - DeepSeek R1 OpenRouter Client
# =====================================================================

import os
import json
import requests
from typing import Dict, Any

# Fetch API Key dynamically from environment variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

def call_deepseek_api(system_prompt: str, user_content: str) -> str:
    """
    Submits claims parameters, policy rules, and context to DeepSeek R1.
    Returns raw reasoning response content string (including thinking trace).
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "Plum Adjudicate"
    }
    
    payload = {
        "model": "deepseek/deepseek-r1:free",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.1
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            res_json = response.json()
            return res_json["choices"][0]["message"]["content"]
            
        # Fallback to paid endpoint if free model queue is overloaded
        payload["model"] = "deepseek/deepseek-r1"
        fallback_resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        if fallback_resp.status_code == 200:
            res_json = fallback_resp.json()
            return res_json["choices"][0]["message"]["content"]
            
        raise Exception(f"OpenRouter DeepSeek API returned status {response.status_code}")
    except Exception as e:
        raise Exception(f"DeepSeek client communication failed: {str(e)}")
