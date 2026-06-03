import os
import json
import requests
from typing import Dict, Any

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

def load_deepseek_prompt() -> str:
    """
    Loads raw DeepSeek R1 system prompt.
    """
    prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", "deepseek_prompt.txt")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r") as f:
            return f.read()
    return "Execute policy compliance rules check."

def clean_deepseek_response(content: str) -> str:
    """
    Strips deepseek thinking trace tags and markdown code blocks.
    """
    cleaned = content
    if "<think>" in cleaned:
        import re
        cleaned = re.sub(r"<think>[\s\S]*?<\/think>", "", cleaned)
    if "```" in cleaned:
        cleaned = cleaned.replace("```json", "").replace("```", "")
    return cleaned.strip()

def run_deepseek_adjudication(extracted_data: Dict[str, Any], policy: Dict[str, Any], rules_text: str) -> Dict[str, Any]:
    """
    Sends extraction JSON payload + Policy + Rules to DeepSeek R1.
    """
    system_prompt = load_deepseek_prompt()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "Plum Adjudicate"
    }
    
    user_payload = f"""
Extracted Document Data:
{json.dumps(extracted_data, indent=2)}

Active Policy Terms Configuration:
{json.dumps(policy, indent=2)}

Adjudication Rules Guidebook:
{rules_text}
"""

    payload = {
        "model": "deepseek/deepseek-r1:free",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_payload}
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
            content = res_json["choices"][0]["message"]["content"]
            cleaned = clean_deepseek_response(content)
            return json.loads(cleaned)
            
        # Retry with non-free model ID
        payload["model"] = "deepseek/deepseek-r1"
        fallback_resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        if fallback_resp.status_code == 200:
            res_json = fallback_resp.json()
            content = res_json["choices"][0]["message"]["content"]
            cleaned = clean_deepseek_response(content)
            return json.loads(cleaned)
            
        raise Exception(f"OpenRouter DeepSeek API returned status {response.status_code}")
        
    except Exception as e:
        print("DeepSeek Adjudication failed, using local rules fallback:", e)
        # Import rule engine logic as fallback
        from .rule_engine import adjudicate_claim_local
        
        # Format claim payload for local adjudicator
        claim_payload = {
            "claim_amount": extracted_data.get("claim_amount", 0.0),
            "member_name": extracted_data.get("patient_name", "Rajesh Kumar"),
            "member_id": "EMP101",
            "hospital": extracted_data.get("hospital_or_clinic"),
            "cashless_request": extracted_data.get("payment_mode") == "Cashless",
            "documents": {
                "prescription": {
                    "doctor_name": extracted_data.get("doctor_name", ""),
                    "doctor_reg": extracted_data.get("doctor_registration_number", ""),
                    "diagnosis": extracted_data.get("diagnosis", ""),
                    "medicines_prescribed": extracted_data.get("medicines"),
                    "procedures": extracted_data.get("procedures")
                },
                "bill": extracted_data.get("bill_breakdown", {})
            }
        }
        
        outcome = adjudicate_claim_local(claim_payload, policy)
        
        return {
            "decision": outcome.get("decision", "MANUAL_REVIEW"),
            "approved_amount": outcome.get("approved_amount", 0.0),
            "deductions": {},
            "rejection_reasons": outcome.get("rejection_reasons", []),
            "policy_violations": [],
            "approved_items": [],
            "rejected_items": outcome.get("rejected_items", []),
            "fraud_flags": outcome.get("flags", []),
            "medical_necessity_analysis": ["Local rules engine fallback executed."],
            "reasoning": [outcome.get("notes", "")],
            "confidence_score": outcome.get("confidence_score", 0.95),
            "next_steps": outcome.get("next_steps", "Re-evaluate when API online.")
        }
