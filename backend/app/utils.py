import json
import re

def repair_json(raw: str) -> str:
    """Remove markdown, extract first balanced JSON, remove trailing commas."""
    raw = re.sub(r'```json\s*', '', raw)
    raw = re.sub(r'```\s*', '', raw)
    start = raw.find('{')
    if start == -1:
        raise ValueError("No JSON object found")
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
        raise ValueError("Unbalanced braces")
    json_str = raw[start:end]
    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)
    return json_str

def safe_json_loads(raw: str) -> dict:
    try:
        return json.loads(raw)
    except Exception:
        repaired = repair_json(raw)
        return json.loads(repaired)