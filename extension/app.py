from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import os
import sys
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        # Include messages that have any detected categories (even if score is 0)
        if categories:
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

    print(f"[DEBUG NLP] Raw text length: {len(raw_text)}")
    print(f"[DEBUG NLP] Extracted messages: {len(extracted)}")
    print(f"[DEBUG NLP] Grouped messages: {len(grouped)}")
    print(f"[DEBUG NLP] Analysis units: {len(analysis_units)}")
    for i, unit in enumerate(analysis_units):
        from NLP.risk_score_message import calculate_message_risk_score
        score, cats = calculate_message_risk_score(unit)
        print(f"[DEBUG NLP]   Unit {i}: {unit[:60]}... Score={score}, Categories={cats}")

    chat_report = analyze_chat(analysis_units)
    summaries = summarize_message_scores(analysis_units)

    print(f"[DEBUG NLP] Chat report detected_categories: {chat_report.get('detected_categories')}")
    print(f"[DEBUG NLP] Message summaries count: {len(summaries)}")
    
    return {
        "extracted_messages": extracted,
        "grouped_messages": grouped,
        "chat_report": chat_report,
        "message_summaries": summaries
    }


def build_flags(chat_report, message_summaries):
    from NLP.scam_keywords import CATEGORIES
    
    # Map internal category names to display names that match popup.js
    CATEGORY_DISPLAY_NAMES = {
        "urgency": "Urgency",
        "identity_threat": "Identity Threat",
        "financial_pressure": "Financial Pressure",
        "authority": "Authority",
        "delivery": "Delivery Scams",
        "promotion": "Promotional Bait",
        "link": "Link Requests"
    }
    
    flags = []

    # Build helper maps
    keyword_to_category = {}
    category_to_keywords = {}
    for category, data in CATEGORIES.items():
        kws = [kw.lower() for kw in data.get("keywords", [])]
        category_to_keywords[category] = kws
        for keyword in kws:
            keyword_to_category[keyword] = category

    # Extract matched keywords from message summaries
    matched_keywords_by_category = {}
    
    # Pass 1: collect per-message detected categories
    for summary in message_summaries:
        detected_cats = summary.get("categories") or []
        if not detected_cats:
            continue

        text = summary["text"].lower()

        # Use only the categories detected for this message to avoid overmatching
        for display_cat in detected_cats:
            # Reverse-map display name back to internal key
            internal_cat = None
            for k, v in CATEGORY_DISPLAY_NAMES.items():
                if v == display_cat:
                    internal_cat = k
                    break
            if not internal_cat:
                continue

            for keyword in category_to_keywords.get(internal_cat, []):
                if keyword in text:
                    if internal_cat not in matched_keywords_by_category:
                        matched_keywords_by_category[internal_cat] = set()
                    matched_keywords_by_category[internal_cat].add(keyword)

    # Pass 2: ensure we gather all keywords for categories detected in the chat
    detected_cats_overall = chat_report.get("detected_categories") or {}
    # Reverse map display label -> internal key
    DISPLAY_TO_INTERNAL = {v: k for k, v in CATEGORY_DISPLAY_NAMES.items()}
    for display_cat in detected_cats_overall.keys():
        internal_cat = DISPLAY_TO_INTERNAL.get(display_cat, display_cat)
        texts_joined = "\n".join(ms["text"].lower() for ms in message_summaries if ms.get("text"))
        for keyword in category_to_keywords.get(internal_cat, []):
            if keyword in texts_joined:
                if internal_cat not in matched_keywords_by_category:
                    matched_keywords_by_category[internal_cat] = set()
                matched_keywords_by_category[internal_cat].add(keyword)
    
    # Add matched keywords as flags grouped by category with display names
    for category, keywords in matched_keywords_by_category.items():
        display_name = CATEGORY_DISPLAY_NAMES.get(category, category)
        sorted_keywords = sorted(keywords)
        joined = ", ".join(sorted_keywords)
        flags.append(f"{display_name} → \"{joined}\"")

    # Add reason if exists
    reason = chat_report.get("reason")
    if reason:
        flags.append(reason.capitalize())

    if not flags:
        flags = ["No suspicious factors detected"]

    print(f"[DEBUG] Detected categories: {chat_report.get('detected_categories')}")
    print(f"[DEBUG] Total flags: {len(flags)}")
    for i, flag in enumerate(flags):
        print(f"[DEBUG] Flag {i}: {flag[:80]}...")
    
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
    """
    Analyze messages for scam risk
    
    Supports two input formats:
    
    1. NEW FORMAT (Extraction Contract):
       {
         "messages": [
           {
             "text": "message content",
             "timestamp": "2025-01-05T10:30:00Z",
             "sender": "unknown",
             "source": "messenger"
           }
         ],
         "image": "base64_encoded_image_optional"
       }
    
    2. LEGACY FORMAT (for backward compatibility):
       {
         "text": "raw text to analyze",
         "image": "base64_encoded_image_optional"
       }
    """
    data = request.json
    image_data = data.get('image', '')
    
    # Support both new message format and legacy text format
    messages = data.get('messages', [])
    raw_text = data.get('text', '')
    
    # If messages are provided, convert to text for NLP pipeline
    if messages and isinstance(messages, list):
        # Extract text from message objects
        raw_text = '\n\n'.join([
            msg['text'] if isinstance(msg, dict) else msg
            for msg in messages
        ])
        print(f"[Extraction Contract] Received {len(messages)} message(s) from {messages[0].get('source', 'unknown') if messages else 'unknown'}")
    
    bank_accounts = BANK_REGEX.findall(raw_text)
    nlp_results = run_nlp_pipeline(raw_text)
    chat_report = nlp_results["chat_report"]
    flags = build_flags(chat_report, nlp_results["message_summaries"])

    risk_score = chat_report["chat_risk_score"]
    
    # Debug: Log the score breakdown
    message_scores_total = sum(msg['score'] for msg in nlp_results["message_summaries"])
    logger.info(f"Chat risk score: {risk_score}, Message summaries total: {message_scores_total}, Messages count: {len(nlp_results['message_summaries'])}")
    
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
        "bank_bonus": bank_bonus,
        "message_count": len(messages) if messages else 1
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

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint - returns service status"""
    return jsonify({
        "status": "ok",
        "service": "Extension Backend",
        "version": "1.0"
    }), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)