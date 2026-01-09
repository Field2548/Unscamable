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

# QR-decoder service URL (configurable via environment variable)
QR_DECODER_URL = os.environ.get('QR_DECODER_URL', 'http://localhost:5001')

BANK_REGEX = re.compile(r"\d{3}-\d{1}-\d{5}-\d{1}")

def format_category_name(category: str) -> str:
    return CATEGORY_LABELS.get(category, category.replace("_", " ").title())


def summarize_message_scores(messages):
    summaries = []
    for msg in messages:
        score, categories, _ = calculate_message_risk_score(msg)
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
        score, cats, _ = calculate_message_risk_score(unit)
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
    flags = []

    # Add category-level summaries
    for label, count in (chat_report.get("detected_categories") or {}).items():
        flags.append(f"{label}")

    # Add reason if exists
    reason = chat_report.get("reason")
    if reason:
        flags.append(reason.capitalize())

    # Add explicit keyword hits per category so the popup can list them all
    matched_keywords = chat_report.get("matched_keywords", {}) or {}
    for label, keywords in matched_keywords.items():
        for kw in keywords:
            if kw:
                flags.append(f"{label} → {kw}")

    # Show all message summaries (including those with score 0 or more)
    # This ensures we capture all instances of detected factors
    # Create separate flags for each category to avoid duplication
    for summary in message_summaries:
        if summary.get("categories"):  # Only show if there are categories
            snippet = summary["text"].strip()
            if len(snippet) > 120:
                snippet = snippet[:117] + "..."
            
            # Create a separate flag for each category
            for category in summary["categories"]:
                flags.append(f"{category} → \"{snippet}\"")

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

def decode_image_with_qr_service(base64_image):
    """
    Send image to QR-decoder service for analysis.
    Returns QR decoding results or None if service is unavailable.
    """
    try:
        qr_payload = {"image": base64_image}
        
        response = requests.post(
            f"{QR_DECODER_URL}/decode",
            json=qr_payload,
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info("[QR] decode success from QR decoder service")
            return response.json()
        else:
            logger.warning(f"⚠️ QR decoder service returned status {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        logger.warning(f"⚠️ QR decoder service unreachable at {QR_DECODER_URL}")
        return None
    except requests.exceptions.Timeout:
        logger.warning("⚠️ QR decoder service request timed out")
        return None
    except Exception as e:
        logger.exception(f"⚠️ QR decoding integration error")
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
    
    # If image is provided, send to QR decoder service for analysis
    qr_results = None
    image_data = data.get('image', '') or ''  # Ensure empty string, not None
    if image_data and image_data.strip():  # Only check if image data is not empty
        logger.info(f"[QR] Image detected in request ({len(image_data)} bytes); sending to QR decoder")
        qr_results = decode_image_with_qr_service(image_data)
        logger.info(f"[QR] Decoder response: {qr_results}")
        if qr_results and qr_results.get('risk_score', 0) > 0:
            qr_score = qr_results.get('risk_score', 0)
            qr_flags = qr_results.get('flags', [])
            logger.info(f"[QR] QR risk score: {qr_score}, Text risk score: {risk_score}, QR flags: {qr_flags}")
            # Combine text and QR decoding risk scores
            combined_score = min(100, risk_score + qr_score)
            logger.info(f"[QR] Combined score: {combined_score}")
            status_info = get_status(combined_score)
            # Add QR flags to main flags list
            if qr_flags:
                flags.extend(qr_flags)
                logger.info(f"[QR] Added {len(qr_flags)} QR flags to response")
            risk_score = combined_score
        elif qr_results:
            # QR was decoded but risk_score is 0; still attach flags if any
            logger.info(f"[QR] QR decoded but risk score is 0")
            qr_flags = qr_results.get('flags', [])
            if qr_flags:
                flags.extend(qr_flags)
                logger.info(f"[QR] Added {len(qr_flags)} QR flags (no score increase)")
            logger.info("[QR] QR decoded but no risk increment applied")
    else:
        logger.info("[QR] No image data in request (screenshot capture may have failed)")
    
    # Only set default "no factors" message if there are truly no flags
    if not flags:
        flags = ["No suspicious factors detected"]
    else:
        logger.info(f"[Analysis] Total flags before response: {len(flags)}: {flags}")

    analysis_detail = {
        **nlp_results,
        "text_risk_score": chat_report["chat_risk_score"],
        "bank_bonus": bank_bonus,
        "message_count": len(messages) if messages else 1,
        # Surface matched keywords for the popup UI
        "matched_keywords": chat_report.get("matched_keywords", {})
    }

    return jsonify({
        "risk_score": risk_score,
        "status": status_info["status"],
        "color": status_info["color"],
        "flags": flags,
        "entities_found": bank_accounts,
        "qr_results": qr_results,
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