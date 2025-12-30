from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import os
import sys
import requests
import json

# Add parent directory to path to import from NLP module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from NLP.scam_keywords import CATEGORIES

app = Flask(__name__)
CORS(app)  # Enable CORS for Chrome extension

# OCR-Scam-Guard service URL (configurable via environment variable)
OCR_SERVICE_URL = os.environ.get('OCR_SERVICE_URL', 'http://localhost:5001')

# Convert CATEGORIES from scam_keywords to PATTERNS format
PATTERNS = [
    {
        "name": category_key.replace('_', ' ').title(),
        "terms": category_data["keywords"],
        "artifacts": [],
        "weight": category_data["weight"]
    }
    for category_key, category_data in CATEGORIES.items()
]

OTP_REGEX = re.compile(r"\b\d{6}\b")
BANK_REGEX = re.compile(r"\d{3}-\d{1}-\d{5}-\d{1}")


def normalize(text: str) -> str:
    return text.lower()


def detect_patterns(text: str):
    text_norm = normalize(text)
    matched = []
    score = 0

    for pattern in PATTERNS:
        has_term = any(term.lower() in text_norm for term in pattern["terms"])
        has_artifact = any(artifact in text_norm for artifact in pattern["artifacts"])
        if has_term or has_artifact:
            matched.append(pattern["name"])
            score += pattern["weight"]

    otp_found = bool(OTP_REGEX.search(text))
    if otp_found:
        matched.append("พบรหัส OTP 6 หลัก")
        score += 8

    return matched, score


def calculate_risk(text, entities):
    matched_patterns, pattern_score = detect_patterns(text)

    score = pattern_score

    if entities:
        score += 15
        matched_patterns.append("พบบัญชีต้องสงสัย")

    if score > 100:
        score = 100

    return score, matched_patterns


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

    risk_score, flags = calculate_risk(raw_text, bank_accounts)
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
        "ocr_results": ocr_results
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)