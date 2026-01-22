def ensure_dict(data):
    if not isinstance(data, dict):
        raise ValueError("Expected dictionary input")

def ensure_list(data):
    if not isinstance(data, list):
        raise ValueError("Expected list input")

def ensure_keys(data, keys):
    for k in keys:
        if k not in data:
            raise ValueError(f"Missing key: {k}")
