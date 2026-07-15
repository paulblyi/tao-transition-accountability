import openai
import json
import logging
from app.config import settings
import requests
import re

__all__ = ['call_llm', 'process_comments']

# ----------------------------------------------------------------------
# Provider setup
# ----------------------------------------------------------------------
if settings.PROVIDER == "gemini":
    from google import genai
    gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
else:
    openai.api_key = settings.OPENAI_API_KEY
    openai.base_url = settings.OPENAI_BASE_URL

print(f"🔍 OpenAI client configured with base_url: {openai.base_url}")

# ----------------------------------------------------------------------
# 1. Helper to call the LLM (supports both OpenAI and Ollama)
# ----------------------------------------------------------------------
def call_llm(prompt: str, max_tokens: int = 500) -> str:
    """
    Call the LLM. If the base URL indicates a local instance (localhost, host.docker.internal, or a private IP),
    use requests directly; otherwise, use the OpenAI client.
    """
    base_url = settings.OPENAI_BASE_URL.lower()
    is_local = (
        "localhost" in base_url or 
        "host.docker.internal" in base_url or 
        "127.0.0.1" in base_url or
        "172." in base_url or
        "192.168." in base_url or
        "10." in base_url
    )
    
    if is_local:
        url = f"{settings.OPENAI_BASE_URL}/chat/completions"
        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.3,
            "stream": False
        }
        try:
            response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=300)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.Timeout:
            logging.error("Ollama request timed out after 300 seconds.")
            raise
        except Exception as e:
            logging.error(f"Ollama request failed: {e}")
            raise
    else:
        messages = [{"role": "user", "content": prompt}]
        response = openai.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content

# ----------------------------------------------------------------------
# 2. Keyword-based fallback summary
# ----------------------------------------------------------------------
def _keyword_fallback_summary(comments_dict: dict, facility_name: str) -> dict:
    """
    Generate a fallback summary using keyword extraction from comments.
    This is used when the LLM call fails.
    """
    if not comments_dict:
        return {
            "summary": f"{facility_name}: No comments available.",
            "categories": [],
            "challenges": [],
            "mitigations": []
        }

    all_text = " ".join([str(v) for v in comments_dict.values() if v and str(v) != 'nan']).lower()

    # Theme keywords
    themes = {
        "staffing": ["staff", "nurse", "personnel", "workforce", "focal person", "officer", "sic", "nic"],
        "training": ["train", "mentorship", "capacity", "skill", "orientation", "ojt", "on-job"],
        "supply chain": ["stock", "commodity", "drug", "order", "supply", "logistics", "procurement", "kit"],
        "community engagement": ["community", "vhw", "village health", "hcc", "committee", "mobilization"],
        "infrastructure": ["facility", "building", "room", "space", "equipment"],
        "governance": ["governance", "accountability", "coordination", "plan", "sustainability", "transition"],
        "defaulter tracking": ["defaulter", "track", "follow-up", "return to care"],
        "viac": ["viac", "cervical", "screening", "hpv", "dna"],
        "hts": ["hts", "hiv testing", "testing", "counsellor", "pc"],
        "prep": ["prep", "prophylaxis"],
        "art": ["art", "antiretroviral", "treatment"]
    }

    detected = []
    for theme, keywords in themes.items():
        if any(kw in all_text for kw in keywords):
            detected.append(theme)

    # Detect negative words for challenges
    negative_words = ["shortage", "lack", "gap", "challenge", "issue", "problem", "stockout", "out of stock", "not available", "weak", "limited"]
    challenges_detected = any(w in all_text for w in negative_words)

    # Build summary
    if detected:
        summary = f"{facility_name}: comments highlight themes including {', '.join(detected)}."
        if challenges_detected:
            summary += " Challenges are mentioned (e.g., resource limitations, gaps)."
        else:
            summary += " No major challenges explicitly mentioned."
    else:
        summary = f"{facility_name}: comments available but could not automatically identify themes. Please review the raw comments."

    return {
        "summary": summary,
        "categories": detected,
        "challenges": ["Challenges mentioned – see comments for details"] if challenges_detected else [],
        "mitigations": []
    }

# ----------------------------------------------------------------------
# 3. Main processing function
# ----------------------------------------------------------------------
def process_comments(comments_dict: dict, facility_name: str = None, total_facilities: int = 1) -> dict:
    """
    Takes a dict of comment fields and returns a structured insight.
    Includes facility context for more specific summaries.
    """
    if not comments_dict:
        return {"summary": "No comments provided.", "categories": [], "challenges": [], "mitigations": []}

    full_text = "\n".join([f"{k}: {v}" for k, v in comments_dict.items() if v and str(v) != 'nan'])
    if not full_text.strip():
        return {"summary": "No meaningful comments.", "categories": [], "challenges": [], "mitigations": []}

    context = ""
    if facility_name:
        context = f"These comments are from the following facility: {facility_name}.\n"
    if total_facilities > 1:
        context = f"These comments are aggregated from {total_facilities} facilities. "

    prompt = f"""
        {context}
        You are an expert in HIV programme transition analysis. Given the following comments from facility visits, produce a JSON output with:
        1. "summary": a concise 2-3 sentence summary of the main points. Be specific and mention the facility name(s) if provided.
        2. "categories": a list of major themes (e.g., Staffing, Supply Chain, Community Engagement, Logistics, Training, Infrastructure).
        3. "challenges": a list of specific challenges mentioned.
        4. "mitigations": a list of mitigation strategies or recommendations.

        Comments:
        {full_text}

        Return only valid JSON, no extra text.
        """
    try:
        response_text = call_llm(prompt)

        # Remove markdown wrappers
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*', '', response_text)

        # Extract only the first valid JSON object
        start = response_text.find('{')
        if start == -1:
            raise ValueError("No JSON object found in response")
        braces = 0
        end = start
        for i in range(start, len(response_text)):
            if response_text[i] == '{':
                braces += 1
            elif response_text[i] == '}':
                braces -= 1
                if braces == 0:
                    end = i + 1
                    break
        if braces != 0:
            raise ValueError("Unbalanced braces in JSON")

        json_str = response_text[start:end]

        # Use safe JSON loading (from utils) if available, otherwise fallback to json.loads
        try:
            from app.utils import safe_json_loads
            result = safe_json_loads(json_str)
        except ImportError:
            result = json.loads(json_str)

        return {
            "summary": result.get("summary", ""),
            "categories": result.get("categories", []),
            "challenges": result.get("challenges", []),
            "mitigations": result.get("mitigations", [])
        }
    except Exception as e:
        logging.error(f"LLM processing failed: {e}")
        # Use keyword-based fallback
        return _keyword_fallback_summary(comments_dict, facility_name or "Facility")