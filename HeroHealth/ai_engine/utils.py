import json

def parse_safely(json_str):
    try:
        return json.loads(json_str)
    except Exception:
        return None
