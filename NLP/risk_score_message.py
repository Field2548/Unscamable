from typing import List, Tuple

try:
    from .scam_keywords import CATEGORIES
    from ._regex import REGEX, REGEX_WEIGHT
except ImportError:  # fallback when running as a loose script
    from scam_keywords import CATEGORIES
    from _regex import REGEX, REGEX_WEIGHT


def _normalize(text: str) -> str:
    """Strip whitespace and punctuation so comparisons ignore spacing/separators."""
    return "".join(ch for ch in text if ch.isalnum())


NORMALIZED_KEYWORDS = {
    category: [_normalize(keyword) for keyword in data["keywords"]]
    for category, data in CATEGORIES.items()
}


def calculate_message_risk_score(message: str) -> Tuple[int, List[str]]:
    """Assign a phishing risk score based on keyword and regex matches."""
    score = 0
    matched_categories_set = set()  # Use set to avoid duplicates
    normalized_message = _normalize(message)

    # Check keywords from categories
    for category, data in CATEGORIES.items():
        normalized_keywords = NORMALIZED_KEYWORDS[category]
        for keyword, normalized_keyword in zip(data["keywords"], normalized_keywords):
            if keyword in message or normalized_keyword in normalized_message:
                score += data["weight"]
                matched_categories_set.add(category)
                break  # prevent double counting same category

    # URL regex (strong signal)
    if REGEX["url"].search(message):
        score += REGEX_WEIGHT["url"]
        matched_categories_set.add("url")

    # Money regex (strong signal)
    if REGEX["money"].search(message):
        score += REGEX_WEIGHT["money"]
        matched_categories_set.add("money")

    # Bonus for multiple manipulation techniques
    matched_categories = list(matched_categories_set)
    if len(matched_categories) >= 3:
        score += 20
    elif len(matched_categories) == 2:
        score += 10

    score = min(score, 100)
    return score, matched_categories