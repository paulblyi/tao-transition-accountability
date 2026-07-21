import openai
import json
import logging
from app.config import settings
import requests
import re
from collections import Counter

__all__ = ['call_llm', 'process_comments', 'process_comments_sampled', 'process_comments_keyword', 'process_comments_chunked']

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
# 2. Analysis Mode: Sampled (fast, reads a sample of comments)
# ----------------------------------------------------------------------
def process_comments_sampled(comment_blocks: list, max_comments: int = 15, max_tokens: int = 500) -> dict:
    """
    Takes a sample of comments (max_comments) and generates a structured insight.
    This is the default, fast mode.
    
    Args:
        comment_blocks: List of comment strings (each with facility/indicator context)
        max_comments: Maximum number of comments to include in the sample
        max_tokens: Maximum tokens for the LLM response
    
    Returns:
        dict: With keys: summary, categories, strengths, challenges, mitigations
    """
    if not comment_blocks:
        return {"summary": "No comments available.", "categories": [], "strengths": [], "challenges": [], "mitigations": []}

    # Take only the first max_comments
    sampled = comment_blocks[:max_comments]
    combined_text = "\n".join(sampled)

    prompt = f"""
You are an expert in HIV programme transition analysis.
Based on the following comments from facility visits, produce a JSON output with:
1. "summary": a concise 2-3 sentence summary of the main points.
2. "categories": a list of major themes (e.g., Staffing, Supply Chain, Community Engagement, Logistics, Training, Infrastructure).
3. "strengths": a list of specific strengths mentioned.
4. "challenges": a list of specific challenges mentioned.
5. "mitigations": a list of mitigation strategies or recommendations.

Comments:
{combined_text}

Return only valid JSON, no extra text.
"""
    try:
        response_text = call_llm(prompt, max_tokens=max_tokens)
        # Clean and parse JSON
        try:
            from app.utils import safe_json_loads
            result = safe_json_loads(response_text)
        except ImportError:
            result = json.loads(response_text)
        return {
            "summary": result.get("summary", ""),
            "categories": result.get("categories", []),
            "strengths": result.get("strengths", []),
            "challenges": result.get("challenges", []),
            "mitigations": result.get("mitigations", [])
        }
    except Exception as e:
        logging.error(f"Sampled LLM processing failed: {e}")
        return {
            "summary": f"Error: {str(e)}",
            "categories": [],
            "strengths": [],
            "challenges": [],
            "mitigations": []
        }


# ----------------------------------------------------------------------
# 3. Analysis Mode: Keyword + Sample (fast, covers all themes)
# ----------------------------------------------------------------------
def process_comments_keyword(comment_blocks: list, max_comments: int = 15, max_tokens: int = 500) -> dict:
    """
    Reads ALL comments to extract the most frequent keywords (themes),
    then reads a sample of comments with the keyword list added to the prompt.
    This ensures no major theme is missed, while keeping speed high.
    
    Args:
        comment_blocks: List of comment strings (each with facility/indicator context)
        max_comments: Maximum number of comments to include in the sample
        max_tokens: Maximum tokens for the LLM response
    
    Returns:
        dict: With keys: summary, categories, strengths, challenges, mitigations
    """
    if not comment_blocks:
        return {"summary": "No comments available.", "categories": [], "strengths": [], "challenges": [], "mitigations": []}

    # Step 1: Extract keywords from ALL comments
    all_text = " ".join(comment_blocks)
    # Extract words of 4+ characters
    words = [w.lower() for w in re.findall(r'\b[a-zA-Z]{4,}\b', all_text)]
    # Remove common stopwords
    stopwords = {'this', 'that', 'with', 'from', 'have', 'were', 'they', 'their', 'will', 'what', 'when', 'more', 'some', 'these', 'which', 'would', 'there', 'could', 'should', 'about', 'into', 'than', 'then', 'them', 'your', 'shall', 'each', 'must', 'most', 'other', 'such', 'only'}
    filtered_words = [w for w in words if w not in stopwords]
    common_keywords = Counter(filtered_words).most_common(10)
    keyword_list = ", ".join([f"{k} ({c})" for k, c in common_keywords])

    # Step 2: Take a sample of comments
    sampled = comment_blocks[:max_comments]
    combined_text = "\n".join(sampled)

    prompt = f"""
You are an expert in HIV programme transition analysis.

**Key themes identified across ALL comments**: {keyword_list}

Based on the following comments from facility visits, produce a JSON output with:
1. "summary": a concise 2-3 sentence summary of the main points.
2. "categories": a list of major themes (use the key themes above as a guide, but only include those that appear in the comments).
3. "strengths": a list of specific strengths mentioned.
4. "challenges": a list of specific challenges mentioned.
5. "mitigations": a list of mitigation strategies or recommendations.

Comments (sample):
{combined_text}

Return only valid JSON, no extra text.
"""
    try:
        response_text = call_llm(prompt, max_tokens=max_tokens)
        try:
            from app.utils import safe_json_loads
            result = safe_json_loads(response_text)
        except ImportError:
            result = json.loads(response_text)
        return {
            "summary": result.get("summary", ""),
            "categories": result.get("categories", []),
            "strengths": result.get("strengths", []),
            "challenges": result.get("challenges", []),
            "mitigations": result.get("mitigations", [])
        }
    except Exception as e:
        logging.error(f"Keyword LLM processing failed: {e}")
        return {
            "summary": f"Error: {str(e)}",
            "categories": [],
            "strengths": [],
            "challenges": [],
            "mitigations": []
        }


# ----------------------------------------------------------------------
# 4. Analysis Mode: Chunked (reads ALL comments, most complete)
# ----------------------------------------------------------------------
def process_comments_chunked(comment_blocks: list, chunk_size: int = 12, max_tokens: int = 300) -> dict:
    """
    Splits all comments into small chunks, processes each chunk to extract themes,
    then merges the results and writes a final summary.
    This reads EVERY comment, ensuring no information is lost.
    
    Args:
        comment_blocks: List of comment strings (each with facility/indicator context)
        chunk_size: Number of comments per chunk
        max_tokens: Maximum tokens for each chunk and final summary
    
    Returns:
        dict: With keys: summary, categories, strengths, challenges, mitigations
    """
    if not comment_blocks:
        return {"summary": "No comments available.", "categories": [], "strengths": [], "challenges": [], "mitigations": []}

    # Step 1: Split into chunks
    chunks = [comment_blocks[i:i+chunk_size] for i in range(0, len(comment_blocks), chunk_size)]
    chunk_results = []

    for i, chunk in enumerate(chunks):
        chunk_text = "\n".join(chunk)
        prompt = f"""
You are an expert in HIV programme transition analysis.
Analyse the following comments and extract:
1. "categories": major themes (e.g., Staffing, Supply Chain, Community Engagement, Logistics, Training, Infrastructure).
2. "strengths": specific strengths mentioned.
3. "challenges": specific challenges mentioned.
4. "mitigations": mitigation strategies or recommendations.

Comments:
{chunk_text}

Return only valid JSON with these four keys.
"""
        try:
            response_text = call_llm(prompt, max_tokens=300)
            try:
                from app.utils import safe_json_loads
                result = safe_json_loads(response_text)
            except ImportError:
                result = json.loads(response_text)
            chunk_results.append({
                "categories": result.get("categories", []),
                "strengths": result.get("strengths", []),
                "challenges": result.get("challenges", []),
                "mitigations": result.get("mitigations", [])
            })
            logging.info(f"Processed chunk {i+1}/{len(chunks)} successfully.")
        except Exception as e:
            logging.error(f"Chunk {i+1} processing failed: {e}")
            continue

    if not chunk_results:
        return {
            "summary": "Could not process any chunks.",
            "categories": [],
            "strengths": [],
            "challenges": [],
            "mitigations": []
        }

    # Step 2: Merge all chunk results (deduplicate)
    merged_categories = set()
    merged_strengths = set()
    merged_challenges = set()
    merged_mitigations = set()

    for chunk in chunk_results:
        merged_categories.update(chunk.get("categories", []))
        merged_strengths.update(chunk.get("strengths", []))
        merged_challenges.update(chunk.get("challenges", []))
        merged_mitigations.update(chunk.get("mitigations", []))

    # Step 3: Write the final summary using the merged data
    final_prompt = f"""
Based on the following extracted and merged themes from ALL comments, write a concise 2-3 sentence summary:

- Categories: {', '.join(merged_categories)}
- Strengths: {', '.join(merged_strengths)}
- Challenges: {', '.join(merged_challenges)}
- Mitigations: {', '.join(merged_mitigations)}

Return only a JSON with:
"summary": a 2-3 sentence summary
"""
    try:
        final_response = call_llm(final_prompt, max_tokens=300)
        try:
            from app.utils import safe_json_loads
            final_result = safe_json_loads(final_response)
        except ImportError:
            final_result = json.loads(final_response)
        return {
            "summary": final_result.get("summary", ""),
            "categories": list(merged_categories),
            "strengths": list(merged_strengths),
            "challenges": list(merged_challenges),
            "mitigations": list(merged_mitigations)
        }
    except Exception as e:
        logging.error(f"Final chunked summary LLM failed: {e}")
        # Fallback: return the merged data without a final narrative summary
        return {
            "summary": "Summary could not be generated. Based on the data, categories, strengths, challenges, and mitigations are listed below.",
            "categories": list(merged_categories),
            "strengths": list(merged_strengths),
            "challenges": list(merged_challenges),
            "mitigations": list(merged_mitigations)
        }


# ----------------------------------------------------------------------
# 5. Keyword-based fallback summary (used when LLM fails in process_comments)
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
# 6. Main processing function (for ETL – per facility)
# ----------------------------------------------------------------------
def process_comments(comments_dict: dict, facility_name: str = None, total_facilities: int = 1) -> dict:
    """
    Takes a dict of comment fields and returns a structured insight.
    Includes facility context for more specific summaries.
    This is the original function used by the ETL for per‑facility processing.
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