"""
Three-tier model routing:
  qwen2.5-coder:14b   → code / debug / file tasks / project building
  deepseek-r1:8b       → reasoning / analysis / planning / comparison
  llama3.1:8b          → general chat / quick answers / casual
"""

from config import MODELS

import json
import requests
from config import MODELS, OLLAMA_BASE

ROUTER_PROMPT = """\
You are an intent classifier. Your ONLY job is to route the user's message to the correct model.
Respond with EXACTLY ONE WORD from the choices below. No explanations. No punctuation.

Choices:
- REASONING : If the user wants to build/create a website, app, UI, frontend, or asks for complex architectural planning, strategy, comparing trade-offs, or deep analysis.
- CODE      : If the user needs raw programming help, debugging, fixing an error string, reading/writing single scripts, or shell commands.
- GENERAL   : If the user asks a simple question (weather, time), casual chat, or basic file manipulation/OS tasks.

User Message:
{msg}
"""

def pick_model(user_message: str) -> str:
    """Use the small router model to classify the intent and pick the best model."""
    prompt = ROUTER_PROMPT.format(msg=user_message)
    
    try:
        resp = requests.post(
            f"{OLLAMA_BASE}/api/generate",
            json={
                "model": MODELS["router"],
                "prompt": prompt,
                "stream": False,
                # Force very short completion to keep it fast
                "options": {"num_predict": 5, "temperature": 0.0}
            },
            timeout=5
        )
        resp.raise_for_status()
        result = resp.json().get("response", "").strip().upper()
        
        # Strip out deepseek think blocks if the user didn't install llama3.2 and hallucinated deepseek as router
        import re
        result = re.sub(r"<think>.*?</think>", "", result, flags=re.DOTALL).strip()
        
        if "REASONING" in result:
            return MODELS["reasoning"]
        if "CODE" in result:
            return MODELS["code"]
        
        return MODELS["general"]
        
    except Exception as e:
        print(f"  [Router fallback due to error: {e}]")
        # Fallback to simple heuristic if router is missing or fails
        msg = user_message.lower()
        if any(w in msg for w in ["website", "build", "frontend", "ui", "design"]):
            return MODELS["reasoning"]
        if any(w in msg for w in ["code", "error", "script", "fix", "bug"]):
            return MODELS["code"]
        return MODELS["general"]


def label(model: str) -> str:
    if model == MODELS["code"]:
        return "💻 coder"
    if model == MODELS["reasoning"]:
        return "🧠 reasoning"
    return "💬 general"
