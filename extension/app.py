from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import os
import sys
import requests
import json

# Add parent directory to path to import from NLP module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'NLP'))
from risk_score_message import calculate_message_risk_score
from risk_score_chat import analyze_chat
from chat_extractor import extract_chat_messages
from chat_normalizer import normalize_chat_messages
from chat_grouper import group_chat_messages
from classify_scam_message import classify_risk

app = Flask(__name__)
CORS(app)  # Enable CORS for Chrome extension

# OCR-Scam-Guard service URL (configurable via environment variable)
OCR_SERVICE_URL = os.environ.get('OCR_SERVICE_URL', 'http://localhost:5001')

BANK_REGEX = re.compile(r"\d{3}-\d{1}-\d{5}-\d{1}")

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


def format_category_label(category: str) -> str:
    return CATEGORY_LABELS.get(category, category.replace("_", " ").title())


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
    is_chat = data.get('is_chat', False)  # flag to determine if analyzing chat or single message
    
    bank_accounts = BANK_REGEX.findall(raw_text)
    
    if is_chat:
        # Full chat analysis pipeline
        extracted_messages = extract_chat_messages(raw_text)
        normalized_messages = normalize_chat_messages(extracted_messages)
        grouped_messages = group_chat_messages(normalized_messages)
        chat_result = analyze_chat(grouped_messages)
        
        risk_score = chat_result["chat_risk_score"]
        flags = list(chat_result["detected_categories"].keys())
        reason = chat_result["reason"]
    else:
        # Single message analysis
        risk_score, categories = calculate_message_risk_score(raw_text)
        flags = [format_category_label(cat) for cat in categories]
        reason = "Single message analysis"
    
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
    
    return jsonify({
        "risk_score": risk_score,
        "status": status_info["status"],
        "color": status_info["color"],
        "flags": flags,
        "entities_found": bank_accounts,
        "reason": reason if is_chat else None,
        "ocr_results": ocr_results
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)