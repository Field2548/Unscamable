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
    "time_pressure": "Time Pressure",
    "otp": "OTP Request",
}

# Set initial chat state 
class ChatState:
    def __init__(self):
        self.total_score = 0
        self.category_counts = {}
        self.messages_seen = 0
        self.unique_categories = set()


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
 
# Fuction for analyzing chat messages
def analyze_chat(chat_messages):
    chat = ChatState()

    for message in chat_messages:
        score, normalized_categories = calculate_message_risk_score(message)

        chat.messages_seen += 1
        chat.total_score += score

        for category in normalized_categories:
            chat.category_counts[category] = chat.category_counts.get(category, 0) + 1
            chat.unique_categories.add(category)

    repetition_bonus = apply_repetition_bonus(chat)
    escalation_bonus = apply_escalation_bonus(chat)

    chat.total_score = min(chat.total_score, 100)

    return build_output(
        chat,
        chat.total_score,
        repetition_bonus,
        escalation_bonus
    )

# Function for repetition bonus       
def apply_repetition_bonus(chat: ChatState):
    repeated_categories = []
    for cat, count in chat.category_counts.items():
        if count >= 3:
            chat.total_score += 15
            repeated_categories.append(cat)
        elif count == 2:
            chat.total_score += 8
            repeated_categories.append(cat)
    return repeated_categories

# Function for escalation bonus
def apply_escalation_bonus(chat: ChatState):
    if len(chat.unique_categories) >= 3:
        chat.total_score += 20
        return True
    elif len(chat.unique_categories) == 2:
        chat.total_score += 10
        return True
    return False

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
def build_output(chat, final_score, repeated_categories, escalated):
    return {
        "chat_risk_score": final_score,
        "risk_level": classify_risk(final_score),
        "detected_categories": format_detected_categories(chat.category_counts),
        "reason": build_reason(chat, repeated_categories, escalated)
    }
