import base64
import os
import re
import traceback
import json

import cv2
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def base64_to_image(base64_string):
    """
    Decodes a base64 string into an OpenCV image.
    Handles 'data:image/jpeg;base64,' headers if present.
    """
    if ',' in base64_string:
        base64_string = base64_string.split(',')[1]
    
    img_data = base64.b64decode(base64_string)
    nparr = np.frombuffer(img_data, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return image


URL_REGEX = re.compile(r"(https?://[^\s]+)", re.IGNORECASE)
SUSPICIOUS_SHORTENERS = ("bit.ly", "tinyurl", "cutt.ly", "goo.gl", "s.id", "t.co")
PAYMENT_KEYWORDS = ("transfer", "payment", "wallet", "bank", "account", "paynow", "promptpay", "qr", "scan", "พร้อมเพย์", "โอนเงิน", "ชำระเงิน")

# Load QR code blacklist
def load_qr_blacklist():
    """Load QR code blacklist from JSON file."""
    try:
        blacklist_path = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'blacklist.json')
        with open(blacklist_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('qr_codes', [])
    except Exception as e:
        print(f"[Warning] Could not load blacklist: {e}")
        return []

QR_BLACKLIST = load_qr_blacklist()
print(f"[Blacklist] Loaded {len(QR_BLACKLIST)} QR code entries")


def decode_qr_payloads(image):
    """Decode one or more QR codes from an image and return any payloads."""
    detector = cv2.QRCodeDetector()
    payloads = []

    try:
        decoded_multi = detector.detectAndDecodeMulti(image)
        if isinstance(decoded_multi, tuple) and len(decoded_multi) >= 2:
            # OpenCV returns (retval, decoded_info, points, straight_qrcode)
            decoded_info = decoded_multi[1]
        else:
            decoded_info = decoded_multi

        if decoded_info:
            payloads.extend([text for text in decoded_info if text])
    except Exception:
        # Fall back to single-code decode if multi fails
        pass

    if not payloads:
        try:
            decoded_single, _ = detector.detectAndDecode(image)
            if decoded_single:
                payloads.append(decoded_single)
        except Exception:
            pass

    return payloads


def check_blacklist(payload):
    """Check if payload matches any blacklisted QR code entry."""
    payload_text = (payload or "").strip()
    payload_normalized = ' '.join(payload_text.split())  # Normalize whitespace
    
    for entry in QR_BLACKLIST:
        # Check account name match (case-insensitive, partial match)
        account_name = entry.get('account_name', '')
        if account_name and account_name.lower() in payload_normalized.lower():
            return True, entry
        
        # Check account number match (flexible matching with and without dashes)
        account_number = entry.get('account_number', '')
        if account_number:
            # Try exact match
            if account_number in payload_text:
                return True, entry
            # Try without dashes
            account_num_clean = account_number.replace('-', '')
            payload_clean = payload_text.replace('-', '').replace(' ', '')
            if account_num_clean in payload_clean:
                return True, entry
        
        # Check ref_id match (exact match, with or without dashes/spaces)
        ref_id = entry.get('ref_id', '')
        if ref_id and (ref_id in payload_text or ref_id in payload_normalized.replace(' ', '')):
            return True, entry
    
    return False, None


def score_payloads(payloads):
    """Compute a simple risk score and flags based on decoded QR payloads."""
    total_risk = 0
    flags = []

    for payload in payloads:
        payload_risk = 0
        payload_text = payload or ""
        
        print(f"[QR Score] Analyzing payload: {repr(payload_text[:100])}")
        
        # Check blacklist first (highest priority)
        is_blacklisted, blacklist_entry = check_blacklist(payload)
        if is_blacklisted:
            payload_risk += 50
            account_name = blacklist_entry.get('account_name', 'Unknown')
            report_count = blacklist_entry.get('report_count', 0)
            flags.append(f"BLACKLISTED QR CODE: {account_name} ({report_count} reports)")
            notes = blacklist_entry.get('notes', '')
            if notes:
                flags.append(f"Reason: {notes}")
            print(f"[QR Score] Blacklist match found: +50 points")
        
        urls = URL_REGEX.findall(payload_text)
        if urls:
            payload_risk += 30
            flags.append(f"QR code links to URL: {urls[0]}")
            print(f"[QR Score] URL detected: +30 points")
            for url in urls:
                lower_url = url.lower()
                for shortener in SUSPICIOUS_SHORTENERS:
                    if shortener in lower_url:
                        payload_risk += 20
                        flags.append(f"Shortened URL detected ({shortener})")
                        print(f"[QR Score] Shortener detected: +20 points")
                        break

        lower_payload = payload_text.lower()
        print(f"[QR Score] Checking payment keywords in: {repr(lower_payload[:100])}")
        for keyword in PAYMENT_KEYWORDS:
            if keyword in lower_payload:
                print(f"[QR Score] Found keyword '{keyword}'")
                break
        
        if any(keyword in lower_payload for keyword in PAYMENT_KEYWORDS):
            payload_risk += 15
            flags.append("Payment-related text detected in QR payload")
            print(f"[QR Score] Payment keywords detected: +15 points")
        else:
            print(f"[QR Score] NO payment keywords found")

        if not urls and payload_text.strip() and not is_blacklisted:
            flags.append("QR payload contains text content")

        print(f"[QR Score] Total for this payload: {payload_risk}")
        total_risk += payload_risk

    # If we decoded something but scored 0, still add a baseline risk to surface it
    if payloads and total_risk == 0:
        total_risk = 10
        flags.append("QR code detected with content")

    print(f"[QR Score] Final score: {min(100, total_risk)}, Flags: {len(flags)}")
    return min(100, total_risk), flags

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint for the extension to verify service is running."""
    return jsonify({"status": "running", "service": "qr-decoder"}), 200

@app.route('/decode', methods=['POST'])
def decode_image():
    try:
        data = request.json or {}
        image_b64 = data.get('image')

        if not image_b64:
            return jsonify({"status": "error", "message": "No image provided"}), 400
        
        image = base64_to_image(image_b64)
        if image is None:
            return jsonify({"status": "error", "message": "Failed to decode image"}), 400

        payloads = decode_qr_payloads(image)
        if not payloads:
            return jsonify({
                "status": "success",
                "decoded_payloads": [],
                "risk_score": 0,
                "flags": ["No QR codes detected"]
            }), 200

        risk_score, flags = score_payloads(payloads)

        result = {
            "status": "success",
            "decoded_payloads": payloads,
            "risk_score": risk_score,
            "flags": flags
        }

        print(f"[QR Decode] Decoded {len(payloads)} QR payload(s). Risk score: {risk_score}")

        return jsonify(result), 200

    except Exception as e:
        print("ERROR: Critical server error")
        traceback.print_exc() # This prints the exact line number of the error
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get('QR_DECODER_PORT', 5001))
    print(f"[Server] QR Decoder running on http://localhost:{port}")
    app.run(port=port, debug=False)
