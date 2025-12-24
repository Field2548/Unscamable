from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for Chrome extension

# Fraud pattern keywords/artifacts grouped by scenario
PATTERNS = [
    {"name": "รางวัล/โชค", "terms": ["คุณถูกรางวัล", "รับโชค", "ของรางวัลมูลค่าสูง"], "artifacts": ["ais", "true", "shopee"], "weight": 7},
    {"name": "บัญชีถูกระงับ", "terms": ["บัญชีถูกระงับ", "ยืนยันตัวตนด่วน"], "artifacts": ["kbank", "scb"], "weight": 7},
    {"name": "พัสดุตกค้าง", "terms": ["พัสดุตกค้าง", "ไม่สามารถจัดส่งได้"], "artifacts": ["kerry", "flash", "ไปรษณีย์ไทย"], "weight": 6},
    {"name": "OTP/ความปลอดภัย", "terms": ["รหัส otp", "ยืนยันความปลอดภัย"], "artifacts": ["line", "facebook"], "weight": 8},
    {"name": "ค่าบริการค้างชำระ", "terms": ["ค้างชำระ", "ระงับบริการ"], "artifacts": ["ใบแจ้งหนี้", "qr code"], "weight": 7},
    {"name": "โปรโมชันพิเศษ", "terms": ["โปรพิเศษ", "วันนี้เท่านั้น"], "artifacts": ["โค้ดส่วนลด"], "weight": 6},
    {"name": "ลงทุน/คริปโต", "terms": ["กำไรการันตี", "ลงทุนน้อย"], "artifacts": ["แพลตฟอร์มลงทุน", "บัญชีม้า", "crypto", "bitcoin"], "weight": 8},
    {"name": "แอบอ้างผู้บริหาร", "terms": ["ช่วยด่วน", "เรื่องลับ"], "artifacts": ["line"], "weight": 6},
    {"name": "หน่วยงานรัฐ", "terms": ["ศาล", "ตำรวจ", "ปปง."], "artifacts": ["เลขคดี", "หน่วยงาน"], "weight": 7},
    {"name": "แบบสอบถามลูกค้า", "terms": ["แบบสอบถาม", "รับของรางวัล"], "artifacts": ["ฟอร์ม", "โลโก้"], "weight": 6},
    {"name": "เงินคืน/Refund", "terms": ["คืนเงิน", "โอนเงินคืน"], "artifacts": ["ลิงก์ธนาคาร", "platform"], "weight": 7},
    {"name": "สมัครงาน/งานออนไลน์", "terms": ["งานพาร์ทไทม์", "รายได้ดี"], "artifacts": ["line oa", "บัญชีรับเงิน"], "weight": 7},
    {"name": "ยืมเงิน/สินเชื่อ", "terms": ["อนุมัติสินเชื่อ", "ไม่เช็กบูโร"], "artifacts": ["บริษัทสินเชื่อ", "เอกสารปลอม"], "weight": 7},
    {"name": "บัญชีโซเชียลถูกแฮก", "terms": ["บัญชีถูกแฮก", "ระงับการใช้งาน"], "artifacts": ["facebook", "ig"], "weight": 7},
    {"name": "การกุศล/บริจาค", "terms": ["ช่วยเหลือด่วน", "บริจาค"], "artifacts": ["มูลนิธิ", "บัญชีรับบริจาค"], "weight": 6},
    {"name": "ค่าปรับจราจร", "terms": ["ค่าปรับ", "ใบสั่งออนไลน์", "ชำระค่าปรับ"], "artifacts": ["ตำรวจจราจร", "qr code"], "weight": 7},
    {"name": "ประกันภัย/เคลมด่วน", "terms": ["กรมธรรม์", "เคลมประกัน", "หมดอายุ"], "artifacts": ["เลขกรมธรรม์", "บริษัทประกัน"], "weight": 7},
    {"name": "สิทธิ์เยียวยา/เงินรัฐ", "terms": ["เงินเยียวยา", "สิทธิ์รัฐ", "ลงทะเบียนด่วน"], "artifacts": ["โครงการรัฐ", ".go.th"], "weight": 7},
    {"name": "แจ้งเตือนแอปจ่ายเงิน", "terms": ["โอนเงินผิดปกติ", "ระงับบัญชีชั่วคราว"], "artifacts": ["truemoney", "promptpay"], "weight": 7},
    {"name": "รางวัลจากบัตรเครดิต", "terms": ["คะแนนสะสม", "แลกรางวัล", "หมดอายุวันนี้"], "artifacts": ["ktc", "scb card"], "weight": 6},
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
        return {"status": "Be cautious", "color": "#9A9C49"}
    else:
        return {"status": "Safe", "color": "#4CAF50"}

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    raw_text = data.get('text', '')
    
    bank_accounts = BANK_REGEX.findall(raw_text)

    risk_score, flags = calculate_risk(raw_text, bank_accounts)
    status_info = get_status(risk_score)
    
    return jsonify({
        "risk_score": risk_score,
        "status": status_info["status"],
        "color": status_info["color"],
        "flags": flags,
        "entities_found": bank_accounts
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)