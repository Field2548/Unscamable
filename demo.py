from pathlib import Path

from Risk_score import calculate_risk_score
from Classification import classify_risk
from scam_message import MESSAGES

output_lines = []

for msg in MESSAGES:
    score, matched_categories = calculate_risk_score(msg)
    line = f"{msg} | scam | {score} | {classify_risk(score)}\n{matched_categories}"
    print(line)
    output_lines.append(line)

Path("demo_output.txt").write_text("\n\n".join(output_lines) + "\n", encoding="utf-8")
    