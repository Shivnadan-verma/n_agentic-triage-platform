def select(engineers, bug):
    """
    Select the best engineer for a bug assignment.
    
    Scoring criteria:
    - Skill match: +30 points per matching skill
    - Product match: +20 points
    - Lower workload: +10 points per bug less than average
    - Rating: +5 points per 0.1 rating above 4.0
    - Acceptance rate: +5 points per 0.1 acceptance rate above 0.85
    """
    if not engineers:
        raise ValueError("No engineers available for assignment")
    
    # Calculate average workload
    avg_workload = sum(e.get("total_no_of_bugs", 0) for e in engineers) / len(engineers)
    
    best_engineer = None
    best_score = -1
    
    bug_product = bug.get("product", "").lower()
    bug_skills = [s.lower() for s in bug.get("skill_set", [])] if isinstance(bug.get("skill_set"), list) else []
    
    for engineer in engineers:
        score = 0
        
        # Product match
        engineer_product = engineer.get("product", "").lower()
        if engineer_product == bug_product:
            score += 20
        
        # Skill match
        engineer_skills = [s.lower() for s in engineer.get("skill_set", [])]
        for skill in bug_skills:
            if skill in engineer_skills:
                score += 30
        
        # Workload (lower is better)
        workload = engineer.get("total_no_of_bugs", 0)
        if workload < avg_workload:
            score += 10 * (avg_workload - workload)
        
        # Rating
        rating = engineer.get("rating", 0)
        if rating > 4.0:
            score += 5 * ((rating - 4.0) * 10)
        
        # Acceptance rate
        acceptance_rate = engineer.get("acceptance_rate", 0)
        if acceptance_rate > 0.85:
            score += 5 * ((acceptance_rate - 0.85) * 10)
        
        if score > best_score:
            best_score = score
            best_engineer = engineer
    
    return best_engineer if best_engineer else engineers[0]
