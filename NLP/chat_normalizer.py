from _regex import EMOJI_REGEX, REPEATED_PUNCT, POLITE_PARTICLES

def normalize_chat_messages(messages: list[str]) -> list[str]:
    normalized = []

    for msg in messages:
        msg = msg.lower()

        # remove emojis
        msg = EMOJI_REGEX.sub("", msg)

        # remove polite fillers
        msg = POLITE_PARTICLES.sub("", msg)

        # normalize punctuation
        msg = REPEATED_PUNCT.sub(r"\1", msg)

        # trim whitespace
        msg = msg.strip()

        if not msg:
            continue

        normalized.append(msg)

    return normalized
