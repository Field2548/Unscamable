from flask import Flask, request, jsonify
from flask_cors import CORS
import re
# import pytesseract # For OCR
# from transformers import pipeline # For NLP

app = Flask(__name__)
CORS(app)  # Enable CORS for Chrome extension

# Mock Risk Scoring Logic
def calculate_risk(text, entities):
    score = 0
    scam_keywords = ["โอนเงิน", "รางวัล", "ด่วน", "ภาษี", "investment"]
    
    for word in scam_keywords:
        if word in text:
            score += 20
    
    # Check against Blacklist (Mockup)
    if "123-456-789" in entities: # Example bank account
        score += 50
    
    # Cap score at 100
    if score > 100:
        score = 100
    
    return score

def get_status(score):
    """Determine status and color based on score"""
    if score >= 70:
        return {"status": "High Risk", "color": "#FF5252"}  # Red
    elif score >= 40:
        return {"status": "Warning", "color": "#FFA726"}  # Orange
    else:
        return {"status": "Be cautious", "color": "#F6FF00"}  # Yellow-Green

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    raw_text = data.get('text', '')
    
    # 1. Preprocessing & Entity Extraction (Regex or NLP)
    # Simple regex for Thai Bank Account patterns
    bank_accounts = re.findall(r'\d{3}-\d{1}-\d{5}-\d{1}', raw_text)
    
    # 2. Risk Scoring
    risk_score = calculate_risk(raw_text, bank_accounts)
    status_info = get_status(risk_score)
    
    return jsonify({
        "risk_score": risk_score,
        "status": status_info["status"],
        "color": status_info["color"],
        "flags": ["Suspicious Keywords"] if risk_score > 30 else [],
        "entities_found": bank_accounts
    })

if __name__ == '__main__':
    app.run(port=5000)