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


def calculate_message_risk_score(message: str) -> Tuple[int, List[str], dict]:
    """Assign a phishing risk score based on keyword and regex matches.

    Returns:
        score: int
        matched_categories: list[str]
        matched_keywords: dict[category, list[str]] (unique keywords per category)
    """
    score = 0
    matched_categories_set = set()  # Use set to avoid duplicates
    matched_keywords = {}
    normalized_message = _normalize(message)

    # Check keywords from categories
    for category, data in CATEGORIES.items():
        normalized_keywords = NORMALIZED_KEYWORDS[category]
        keyword_matches = 0
        for keyword, normalized_keyword in zip(data["keywords"], normalized_keywords):
            if keyword in message or normalized_keyword in normalized_message:
                keyword_matches += 1
                matched_keywords.setdefault(category, set()).add(keyword)
        
        if keyword_matches > 0:
            # Base weight for the category
            score += data["weight"]
            matched_categories_set.add(category)
            
            # Bonus for multiple keywords in same category (indicates strong signal)
            if keyword_matches >= 3:
                score += 10  # 3+ keywords in same category
            elif keyword_matches == 2:
                score += 5   # 2 keywords in same category

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
    # Convert keyword sets to lists for JSON friendliness
    matched_keywords_list = {cat: sorted(list(keywords)) for cat, keywords in matched_keywords.items()}
    return score, matched_categories, matched_keywords_list