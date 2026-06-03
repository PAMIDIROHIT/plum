# =====================================================================
# LLM Layer - Prompt Template Manager
# =====================================================================

import os

def load_prompt_by_name(prompt_name: str) -> str:
    """
    Loads raw text prompt files from the centralized backend prompts directory.
    """
    prompt_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "prompts",
        prompt_name
    )
    if os.path.exists(prompt_path):
        with open(prompt_path, "r") as f:
            return f.read()
    return "Execute pipeline task."
