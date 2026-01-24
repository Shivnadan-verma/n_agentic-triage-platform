def impact_score(severity: str) -> int:
    sev = (severity or "").strip().lower()
    if sev in ("critical", "high"):
        return 80
    return 40
