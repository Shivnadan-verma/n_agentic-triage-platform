def ensure_dict(x, name="input"):
    if not isinstance(x, dict):
        raise ValueError(f"{name} must be a dict")

def ensure_list(x, name="input"):
    if not isinstance(x, list):
        raise ValueError(f"{name} must be a list")

def ensure_keys(d: dict, keys: list[str], name="payload"):
    missing = [k for k in keys if k not in d]
    if missing:
        raise ValueError(f"{name} missing keys: {missing}")
