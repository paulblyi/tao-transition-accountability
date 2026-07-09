import openai
import json
import logging
from app.config import settings
import requests

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
    # If we are using Ollama (local)
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
            # 👇 Added timeout (120 seconds)
            response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=120)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.Timeout:
            logging.error("Ollama request timed out after 120 seconds.")
            raise
        except Exception as e:
            logging.error(f"Ollama request failed: {e}")
            raise
    else:
        # OpenAI / cloud provider via OpenAI client
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
def process_comments(comments_dict: dict) -> dict:
    """
    Takes a dict of comment fields and returns a structured insight.
    """
    if not comments_dict:
        return {"summary": "No comments provided.", "categories": [], "challenges": [], "mitigations": []}

    # Combine all comment values into one text block
    full_text = "\n".join([f"{k}: {v}" for k, v in comments_dict.items() if v and str(v) != 'nan'])
    if not full_text.strip():
        return {"summary": "No meaningful comments.", "categories": [], "challenges": [], "mitigations": []}

    # Skip API key check when using Ollama (local)
    if settings.PROVIDER != "openai" and not settings.OPENAI_API_KEY:
        logging.warning("No OPENAI_API_KEY set. Skipping LLM processing.")
        return {
            "summary": "OpenAI API key not set. Please set OPENAI_API_KEY to enable insights.",
            "categories": [],
            "challenges": [],
            "mitigations": []
        }

    prompt = f"""
        You are an expert in HIV programme transition analysis. Given the following comments from a facility visit, produce a JSON output with:
        1. "summary": a concise 2-3 sentence summary of the main points.
        2. "categories": a list of major themes (e.g., Staffing, Supply Chain, Community Engagement, Logistics, Training, Infrastructure).
        3. "challenges": a list of specific challenges mentioned.
        4. "mitigations": a list of mitigation strategies or recommendations.

        Comments:
        {full_text}

        Return only valid JSON, no extra text.
        """
    try:
        response_text = call_llm(prompt)
        
        # Clean up potential markdown wrappers
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
            
        # Attempt to parse JSON
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError as e:
            logging.warning(f"JSON decode error: {e}\nResponse text: {response_text[:200]}...")
            # Fallback: store raw text as summary
            return {
                "summary": f"Raw response (parsing failed): {response_text[:200]}...",
                "categories": [],
                "challenges": [],
                "mitigations": []
            }
        return {
            "summary": result.get("summary", ""),
            "categories": result.get("categories", []),
            "challenges": result.get("challenges", []),
            "mitigations": result.get("mitigations", [])
        }
    except Exception as e:
        logging.error(f"LLM processing failed: {e}")
        return {"summary": f"Error: {str(e)}", "categories": [], "challenges": [], "mitigations": []}