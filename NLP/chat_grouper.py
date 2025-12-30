from typing import List

try:
    from .risk_score_message import calculate_message_risk_score
except ImportError:  # fallback when executed as a loose script
    from risk_score_message import calculate_message_risk_score

CONTINUATION_KEYWORDS = {
    "กรุณา", "โปรด", "ภายใน", "วันนี้", "ด่วน", "ทันที",
    "คลิก", "กด", "ยืนยัน", "ตรวจสอบ", "เพื่อ", "หากไม่"
}

SHORT_MESSAGE_LEN = 25

STOP_KEYWORDS = {
    "ขอบคุณ", "ขอบคุณครับ", "ขอบคุณค่ะ",
    "โอเค", "ok", "รับทราบ",
    "ได้ครับ", "ได้ค่ะ",
    "สวัสดี", "hello", "hi"
}

URGENCY_HEADER_KEYWORDS = {"ด่วน", "urgent", "important", "แจ้งเตือน"}

def is_urgency_header(msg: str, categories: set) -> bool:
    normalized = msg.strip().lower()
    normalized_categories = {cat.lower() for cat in categories}

    return (
        len(normalized) <= 20
        and normalized_categories == {"urgency"}
        and any(kw in normalized for kw in URGENCY_HEADER_KEYWORDS)
    )


def should_merge(prev_msg: str, curr_msg: str,
                 prev_categories: set, curr_categories: set) -> bool:

    normalized = curr_msg.strip().lower()

    # ❌ HARD STOP
    for stop in STOP_KEYWORDS:
        if stop in normalized:
            return False

    # Rule 1: continuation keywords
    if any(kw in normalized for kw in CONTINUATION_KEYWORDS):
        return True

    # Rule 2: category continuity
    if prev_categories & curr_categories:
        return True

    # Rule 3: short fragment after scam
    if len(normalized) <= SHORT_MESSAGE_LEN and prev_categories:
        return True

    return False


def is_stop_message(msg: str) -> bool:
    normalized = msg.strip().lower()

    # length-based guard
    if len(normalized) > 15:
        return False

    return normalized in STOP_KEYWORDS


def group_chat_messages(messages: List[str]) -> List[str]:
    if not messages:
        return []

    grouped = []
    current_group = None
    prev_categories = set()
    pending_urgency = False 

    for msg in messages:
        # 🚨 HARD STOP
        if is_stop_message(msg):
            if current_group:
                grouped.append(current_group)
            grouped.append(msg)
            current_group = None
            prev_categories = set()
            pending_urgency = False
            continue

        _, curr_categories = calculate_message_risk_score(msg)
        curr_categories = set(curr_categories)

        # 🚨 URGENCY HEADER (buffer it)
        if current_group is None and is_urgency_header(msg, curr_categories):
            current_group = msg
            pending_urgency = True
            prev_categories = set()
            continue

        # START new group
        if current_group is None:
            current_group = msg
            prev_categories = curr_categories
            continue

        # ✅ FORCE-MERGE after urgency header
        if pending_urgency:
            current_group += " " + msg
            prev_categories |= curr_categories
            pending_urgency = False
            continue

        # NORMAL merge logic
        if should_merge(current_group, msg, prev_categories, curr_categories):
            current_group += " " + msg
            prev_categories |= curr_categories
        else:
            grouped.append(current_group)
            current_group = msg
            prev_categories = curr_categories

    if current_group:
        grouped.append(current_group)

    return grouped
