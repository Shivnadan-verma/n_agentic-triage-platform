def score_engineer(engineer: dict, bug: dict) -> float:
    score = 0.0

    # Product match is the biggest signal
    if engineer.get("product") == bug.get("product"):
        score += 30

    # Rating, acceptance, and workload balancing
    score += float(engineer.get("rating", 0)) * 5
    score += float(engineer.get("acceptance_rate", 0)) * 25
    score += max(0.0, 20.0 - float(engineer.get("total_no_of_bugs", 0)))

    return score


def pick_best(engineers: list[dict], bug: dict) -> dict:
    if not engineers:
        raise ValueError("No engineers available")
    return sorted(engineers, key=lambda e: score_engineer(e, bug), reverse=True)[0]
