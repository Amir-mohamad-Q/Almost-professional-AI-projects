import os
import sys

from google import genai
from google.genai import types


api_key = os.getenv("GEMINI_API_KEY", "")
if not api_key:
    print("ERROR: GEMINI_API_KEY is not set. Define it in your environment or .env file.")
    sys.exit(1)

client = genai.Client(api_key=api_key)

DEFAULT_SYSTEM_INSTRUCTION = (
    "You are a precise, comprehensive assistant. Provide accurate, complete, and concise answers with clear structure."
)


def call_llm(prompt, model="gemini-2.5-flash", system_instruction=DEFAULT_SYSTEM_INSTRUCTION):
    combined_prompt = f"{system_instruction}\n\n{prompt}" if system_instruction else prompt
    response = client.models.generate_content(
        model=model,
        contents=combined_prompt,
    )
    # Prefer response.text; if missing, try to extract from candidates
    if getattr(response, "text", None):
        return response.text
    try:
        # google-genai may return candidates with parts
        candidates = getattr(response, "candidates", []) or []
        for cand in candidates:
            parts = getattr(cand, "content", {}).get("parts") if hasattr(cand, "content") else None
            if parts:
                texts = [getattr(p, "text", "") for p in parts if getattr(p, "text", "")]
                if texts:
                    return "\n".join(texts)
    except Exception:
        pass
    return ""