import openai
import json
import logging
from app.config import settings
import requests

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
    Call the LLM. If the base URL indicates a local Ollama instance,
    use requests directly; otherwise, use the OpenAI client.
    """
    if "host.docker.internal" in settings.OPENAI_BASE_URL or "localhost" in settings.OPENAI_BASE_URL:
        url = f"{settings.OPENAI_BASE_URL}/chat/completions"
        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.3,
            "stream": False
        }
        try:
            # ⬆️ Increased timeout to 300 seconds
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
# 2. Main processing function
# ----------------------------------------------------------------------
def process_comments(comments_dict: dict, facility_name: str = None, total_facilities: int = 1) -> dict:
    """Process comments and return structured insight."""
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

        import re
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*', '', response_text)
        
        start = response_text.find('{')
        end = response_text.rfind('}')
        if start != -1 and end != -1 and end > start:
            json_str = response_text[start:end+1]
        else:
            raise ValueError("No valid JSON object found in response")
        
        result = json.loads(json_str)
        
        return {
            "summary": result.get("summary", ""),
            "categories": result.get("categories", []),
            "challenges": result.get("challenges", []),
            "mitigations": result.get("mitigations", [])
        }
    except Exception as e:
        logging.error(f"LLM processing failed: {e}")
        return {"summary": f"Error: {str(e)}", "categories": [], "challenges": [], "mitigations": []}