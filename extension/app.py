from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import os
import sys
import requests

# Add parent directory to path to import from NLP module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from NLP.chat_extractor import extract_chat_messages
from NLP.chat_grouper import group_chat_messages
from NLP.risk_score_chat import analyze_chat, CATEGORY_LABELS
from NLP.risk_score_message import calculate_message_risk_score

app = Flask(__name__)
CORS(app)  # Enable CORS for Chrome extension

# OCR-Scam-Guard service URL (configurable via environment variable)
OCR_SERVICE_URL = os.environ.get('OCR_SERVICE_URL', 'http://localhost:5001')

BANK_REGEX = re.compile(r"\d{3}-\d{1}-\d{5}-\d{1}")

def format_category_name(category: str) -> str:
    return CATEGORY_LABELS.get(category, category.replace("_", " ").title())


def summarize_message_scores(messages):
    summaries = []
    for msg in messages:
        score, categories = calculate_message_risk_score(msg)
        if score <= 0:
            continue

        formatted_categories = [format_category_name(cat) for cat in categories]
        summaries.append({
            "text": msg,
            "score": score,
            "categories": formatted_categories or ["Suspicious activity"]
        })
    return summaries


def run_nlp_pipeline(raw_text: str):
    if not raw_text:
        empty_report = analyze_chat([])
        return {
            "extracted_messages": [],
            "grouped_messages": [],
            "chat_report": empty_report,
            "message_summaries": []
        }

    extracted = extract_chat_messages(raw_text)
    grouped = group_chat_messages(extracted) if extracted else []
    analysis_units = grouped if grouped else extracted

    chat_report = analyze_chat(analysis_units)
    summaries = summarize_message_scores(analysis_units)

    return {
        "extracted_messages": extracted,
        "grouped_messages": grouped,
        "chat_report": chat_report,
        "message_summaries": summaries
    }


def build_flags(chat_report, message_summaries):
    flags = []

    for label, count in (chat_report.get("detected_categories") or {}).items():
        flags.append(f"{label}: detected in {count} message(s)")

    reason = chat_report.get("reason")
    if reason:
        flags.append(reason.capitalize())

    for summary in message_summaries[:3]:  # show up to 3 sample snippets
        categories = ", ".join(summary["categories"])
        snippet = summary["text"].strip()
        if len(snippet) > 120:
            snippet = snippet[:117] + "..."
        flags.append(f"{categories} → \"{snippet}\" (+{summary['score']} pts)")

    return flags


def get_status(score):
    if score > 70: #71-100
        return {"status": "High Risk", "color": "#FF5252"}
    elif score > 40: #41-70
        return {"status": "Warning", "color": "#FFA726"}
    elif score > 0: #1-40
        return {"status": "Be cautious", "color": "#DECA30"}
    else:
        return {"status": "Safe", "color": "#4CAF50"}

def analyze_image_with_ocr(base64_image):
    """
    Send image to OCR-Scam-Guard service for analysis.
    Returns OCR analysis results or None if service is unavailable.
    """
    try:
        ocr_payload = {
            "image": base64_image
        }
        
        response = requests.post(
            f"{OCR_SERVICE_URL}/scan",
            json=ocr_payload,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"⚠️ OCR service returned status {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        print(f"⚠️ OCR service unreachable at {OCR_SERVICE_URL}")
        return None
    except requests.exceptions.Timeout:
        print("⚠️ OCR service request timed out")
        return None
    except Exception as e:
        print(f"⚠️ OCR integration error: {str(e)}")
        return None


@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    raw_text = data.get('text', '')
    image_data = data.get('image', '')
    
    bank_accounts = BANK_REGEX.findall(raw_text)
    nlp_results = run_nlp_pipeline(raw_text)
    chat_report = nlp_results["chat_report"]
    flags = build_flags(chat_report, nlp_results["message_summaries"])

    risk_score = chat_report["chat_risk_score"]
    bank_bonus = 15 if bank_accounts else 0
    if bank_accounts:
        flags.append("พบรูปแบบเลขบัญชีที่อาจเกี่ยวข้องกับการหลอกลวง")

    risk_score = min(100, risk_score + bank_bonus)
    status_info = get_status(risk_score)
    
    # If image is provided, send to OCR service for analysis
    ocr_results = None
    if image_data:
        ocr_results = analyze_image_with_ocr(image_data)
        if ocr_results and ocr_results.get('risk_score', 0) > 0:
            # Combine text and OCR risk scores
            combined_score = min(100, risk_score + ocr_results.get('risk_score', 0))
            status_info = get_status(combined_score)
            if ocr_results.get('flags'):
                flags.extend(ocr_results['flags'])
            risk_score = combined_score
    
    if not flags:
        flags = ["No suspicious factors detected"]

    analysis_detail = {
        **nlp_results,
        "text_risk_score": chat_report["chat_risk_score"],
        "bank_bonus": bank_bonus
    }

    return jsonify({
        "risk_score": risk_score,
        "status": status_info["status"],
        "color": status_info["color"],
        "flags": flags,
        "entities_found": bank_accounts,
        "ocr_results": ocr_results,
        "analysis": analysis_detail
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)