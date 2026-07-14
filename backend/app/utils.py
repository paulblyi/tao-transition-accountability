import json
import re

def repair_json(raw: str) -> str:
    """
    Attempt to repair a malformed JSON string.
    Returns a cleaned JSON string or raises an exception.
    """
    # Remove markdown code fences
    raw = re.sub(r'```json\s*', '', raw)
    raw = re.sub(r'```\s*', '', raw)

    # Find the first '{' and the matching '}' by counting braces
    start = raw.find('{')
    if start == -1:
        raise ValueError("No JSON object found in response")
    braces = 0
    end = start
    for i in range(start, len(raw)):
        if raw[i] == '{':
            braces += 1
        elif raw[i] == '}':
            braces -= 1
            if braces == 0:
                end = i + 1
                break
    if braces != 0:
        raise ValueError("Unbalanced braces in JSON")
    json_str = raw[start:end]

    # Remove trailing commas inside objects/arrays (simple approach)
    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)

    # Try to fix unescaped quotes inside strings (naive but works often)
    # We'll parse with json.loads and if it fails, we fall back to returning the raw text as a summary.
    return json_str

def safe_json_loads(raw: str) -> dict:
    """Try to load JSON with repair; return a dict or raise."""
    try:
        json_str = repair_json(raw)
        return json.loads(json_str)
    except Exception as e:
        # If all fails, raise with the original error
        raise ValueError(f"JSON parsing failed: {e}\nRaw: {raw[:200]}...")