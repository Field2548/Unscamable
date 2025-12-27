from pathlib import Path

try:
    from .risk_score_message import calculate_message_risk_score
    from .classify_scam_message import classify_risk
    from .scam_messages import MESSAGES
except ImportError:  # running as standalone script
    from risk_score_message import calculate_message_risk_score
    from classify_scam_message import classify_risk
    from scam_messages import MESSAGES

output_lines = []

for msg in MESSAGES:
    score, matched_categories = calculate_message_risk_score(msg)
    line = f"{msg} | scam | {score} | {classify_risk(score)}\n{matched_categories}"
    print(line)
    output_lines.append(line)

Path("NLP/demo_output.txt").write_text("\n\n".join(output_lines) + "\n", encoding="utf-8")
    