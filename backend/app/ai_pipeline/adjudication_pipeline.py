# =====================================================================
# AI Pipeline - Claim Adjudication Reasoning Pipeline
# =====================================================================

import json
import re
from typing import Dict, Any
from ..llm.prompt_manager import load_prompt_by_name
from ..llm.deepseek_client import call_deepseek_api, safe_json_parse


def clean_thinking_tags(content: str) -> str:
    """
    Strips reasoning logic thinking tags and markdown brackets from LLM output.
    """
    cleaned = content
    if "<think>" in cleaned:
        cleaned = re.sub(r"<think>[\s\S]*?<\/think>", "", cleaned)
    if "```" in cleaned:
        cleaned = cleaned.replace("```json", "").replace("```", "")
    return cleaned.strip()

def run_adjudication_pipeline(claim_payload: Dict[str, Any], policy: Dict[str, Any], rules_text: str) -> Dict[str, Any]:
    """
    Orchestrates DeepSeek R1 rule adjudication.
    Falls back to local programmatic rule engine on api failures.
    """
    try:
        system_prompt = load_prompt_by_name("adjudication_prompt.txt")
        user_payload = f"""
Extracted Document Data:
{json.dumps(claim_payload, indent=2)}

Active Policy Terms Configuration:
{json.dumps(policy, indent=2)}

Adjudication Rules Guidebook:
{rules_text}
"""
        raw_response = call_deepseek_api(system_prompt, user_payload)
        cleaned = clean_thinking_tags(raw_response)
        return safe_json_parse(cleaned)

    except Exception as e:
        print("DeepSeek Adjudication pipeline failed, falling back to local engine:", e)
        # Import local rules executor as fallback
        from ..adjudication.claim_adjudicator import run_local_adjudication_flow
        
        outcome = run_local_adjudication_flow(claim_payload, policy)
        
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
