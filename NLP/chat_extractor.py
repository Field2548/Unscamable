import re
from _regex import TIMESTAMP_REGEX, DATE_REGEX

SENDER_NOISE = {
    "you", "me", "ฉัน", "ผม", "เรา", "คุณ", "คุณลุกค้า", "customer", "agent",
    "facebook", "messenger", "system", "admin", "administrator", "support"
}
SENDER_NOISE = {s.lower() for s in SENDER_NOISE}


def extract_chat_messages(raw_chat) -> list[str]:
    if isinstance(raw_chat, str):
        lines = raw_chat.splitlines()
    elif isinstance(raw_chat, list):
        lines = []
        for entry in raw_chat:
            if isinstance(entry, str):
                lines.extend(entry.splitlines())
            else:
                raise ValueError("raw_chat list entries must be str")
    else:
        raise ValueError("raw_chat must be str or list[str]")

    messages = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        line = DATE_REGEX.sub("", line)    
        line = TIMESTAMP_REGEX.sub("", line)
        line = line.strip().strip(",;:")
        line = re.sub(r"\s{2,}", " ", line)

        if not line:
            continue

        stripped_tail = line.rstrip(" ,;:")
        head, sep, tail = stripped_tail.rpartition(" ")
        candidate = tail.lower().strip(" ,;:") if sep else stripped_tail.lower().strip(" ,;:")
        if candidate in SENDER_NOISE:
            if not sep:
                continue
            line = head.strip().strip(",;:")
            if not line:
                continue

        line = line.strip().strip(",;:")
        if not line:
            continue

        if len(line) == 0:
            continue

        messages.append(line)

    return messages
