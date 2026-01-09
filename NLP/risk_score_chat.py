try:
    from .risk_score_message import calculate_message_risk_score
    from .classify_scam_message import classify_risk
except ImportError:  # running as standalone script
    from risk_score_message import calculate_message_risk_score
    from classify_scam_message import classify_risk

CATEGORY_LABELS = {
    "urgency": "Urgency",
    "identity_threat": "Identity Threat",
    "financial_pressure": "Financial Pressure",
    "authority": "Authority",
    "delivery": "Delivery Scams",
    "promotion": "Promotional Bait",
    "link": "Link Requests",
    "url": "Suspicious URL",
    "money": "Money Mentions",
}

# Set initial chat state 
class ChatState:
    def __init__(self):
        self.total_score = 0
        self.category_counts = {}
        self.messages_seen = 0
        self.unique_categories = set()
        self.matched_keywords = {}


def format_category_label(category: str) -> str:
    return CATEGORY_LABELS.get(category, category.replace("_", " ").title())


def human_join(parts):
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + f" and {parts[-1]}"


def format_detected_categories(counts):
    return {
        format_category_label(category): count
        for category, count in counts.items()
    }


# Function for analyzing chat messages
def analyze_chat(chat_messages):
    chat = ChatState()

    for message in chat_messages:
        score, normalized_categories, matched_keywords = calculate_message_risk_score(message)

        chat.messages_seen += 1
        # Cap individual message score at 100 before adding
        chat.total_score += min(score, 100)

        for category in normalized_categories:
            chat.category_counts[category] = chat.category_counts.get(category, 0) + 1
            chat.unique_categories.add(category)

        # Track matched keywords per category for UI display
        for category, keywords in (matched_keywords or {}).items():
            label = format_category_label(category)
            if label not in chat.matched_keywords:
                chat.matched_keywords[label] = set()
            chat.matched_keywords[label].update(keywords)

    # Apply bonuses AFTER all messages are processed
    repetition_bonus_details, repetition_bonus_points = apply_repetition_bonus(chat)
    escalation_info = apply_escalation_bonus(chat)

    # Final cap at 100
    chat.total_score = min(chat.total_score, 100)

    return build_output(
        chat,
        chat.total_score,
        repetition_bonus_details,
        escalation_info
    )


# Function for repetition bonus       
def apply_repetition_bonus(chat: ChatState):
    """
    Apply bonus points when the same category appears across multiple messages.
    This indicates persistent manipulation tactics.
    
    Scoring logic:
    - 2 messages in same category: +8 points
    - 3 messages in same category: +15 points
    - 4 messages in same category: +20 points
    - 5+ messages in same category: +25 points (capped)
    """
    repeated_categories = []
    repetition_bonus_points = 0
    for cat, count in chat.category_counts.items():
        bonus = 0
        if count >= 5:
            bonus = 25
        elif count == 4:
            bonus = 20
        elif count == 3:
            bonus = 15
        elif count == 2:
            bonus = 8
        
        if bonus > 0:
            chat.total_score += bonus
            repetition_bonus_points += bonus
            repeated_categories.append((cat, count, bonus))
    
    return repeated_categories, repetition_bonus_points


# Function for escalation bonus
def apply_escalation_bonus(chat: ChatState):
    if len(chat.unique_categories) >= 3:
        chat.total_score += 20
        return True, 20
    elif len(chat.unique_categories) == 2:
        chat.total_score += 10
        return True, 10
    return False, 0


# Function to build output
def build_reason(chat, repeated_categories, escalated):
    reasons = []

    if repeated_categories:
        friendly = [format_category_label(cat).lower() for cat in repeated_categories]
        reasons.append(f"Repeated {human_join(friendly)}")

    if escalated:
        reasons.append("urgency escalation")

    if not reasons:
        return "Suspicious scam patterns detected"

    return " with ".join(reasons)


# output formatter
def build_output(chat, final_score, repeated_categories, escalation_info):
    escalated, escalation_bonus = escalation_info if isinstance(escalation_info, tuple) else (escalation_info, 0)
    
    # Calculate total repetition bonus
    repetition_bonus_points = sum(points for _, _, points in repeated_categories) if repeated_categories else 0
    
    return {
        "chat_risk_score": final_score,
        "risk_level": classify_risk(final_score),
        "detected_categories": format_detected_categories(chat.category_counts),
        "matched_keywords": {label: sorted(list(keywords)) for label, keywords in chat.matched_keywords.items()},
        "reason": build_reason(chat, [cat[0] for cat in repeated_categories] if repeated_categories else [], escalated),
        "repetition_bonus_details": repeated_categories,
        "repetition_bonus_points": repetition_bonus_points,
        "escalation_bonus": escalation_bonus,
        "escalation_bonus_points": escalation_bonus,
        "total_unique_categories": len(chat.unique_categories)
    }
