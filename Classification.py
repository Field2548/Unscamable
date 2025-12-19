def classify_risk(score: int) -> str:
    if score >= 70:
        return "HIGH_RISK"
    elif score >= 40:
        return "WARNING"
    else:
        return "BE CAUTIOUS"