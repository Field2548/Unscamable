"""
ตัวอย่างการใช้ NLP module เพื่อ detect ข้อความและเก็บผลลัพธ์ใน list
Example of using NLP module to detect messages and store results in a list
"""

from risk_score_message import calculate_message_risk_score
from classify_scam_message import classify_risk

# ========================================
# ตัวแปรสำหรับเก็บข้อความที่มีความเสี่ยง
# ========================================

# เก็บเฉพาะข้อความที่มีความเสี่ยง (score >= 40)
RISKY_MESSAGES = []


# ========================================
# ฟังก์ชันจัดการตัวแปร RISKY_MESSAGES
# ========================================

def add_risky_message(message: str):
    """
    ตรวจสอบข้อความและเก็บลงใน RISKY_MESSAGES ถ้ามีความเสี่ยง
    
    Args:
        message: ข้อความที่ต้องการตรวจสอบ
    
    Returns:
        dict ของข้อมูลข้อความ ถ้ามีความเสี่ยง, None ถ้าไม่มีความเสี่ยง
    """
    score, categories = calculate_message_risk_score(message)
    
    # เก็บเฉพาะข้อความที่มีความเสี่ยง (score >= 40)
    if score >= 40:
        risk_level = classify_risk(score)
        data = {
            'message': message,
            'score': score,
            'risk_level': risk_level,
            'categories': categories
        }
        RISKY_MESSAGES.append(data)
        return data
    
    return None


def get_risky_messages():
    """ดึงข้อความที่มีความเสี่ยงทั้งหมด"""
    return RISKY_MESSAGES


def clear_risky_messages():
    """ล้างข้อมูลในตัวแปร RISKY_MESSAGES"""
    RISKY_MESSAGES.clear()


def count_risky_messages():
    """นับจำนวนข้อความที่มีความเสี่ยง"""
    return len(RISKY_MESSAGES)


# ========================================
# ฟังก์ชันสำหรับ detect ข้อความ
# ========================================

# ตัวอย่างที่ 1: Detect ข้อความหลายๆ ข้อความแล้วเก็บผลลัพธ์
def detect_multiple_messages(messages: list) -> list:
    """
    รับ list ของข้อความ แล้ว return list ของผลลัพธ์
    
    Args:
        messages: list ของข้อความที่ต้องการตรวจสอบ
    
    Returns:
        list ของ dict ที่มีข้อมูล: message, score, risk_level, categories
    """
    results = []
    
    for message in messages:
        score, categories = calculate_message_risk_score(message)
        risk_level = classify_risk(score)
        
        results.append({
            'message': message,
            'score': score,
            'risk_level': risk_level,
            'categories': categories
        })
    
    return results


# ตัวอย่างที่ 2: Detect แล้วกรองเฉพาะที่มีความเสี่ยง
def detect_and_filter_risky(messages: list, min_score: int = 40) -> list:
    """
    ตรวจสอบข้อความและเก็บเฉพาะที่มี risk score >= min_score
    
    Args:
        messages: list ของข้อความที่ต้องการตรวจสอบ
        min_score: คะแนนขั้นต่ำที่จะถูกเก็บไว้ (default: 40)
    
    Returns:
        list ของข้อความที่มีความเสี่ยง
    """
    risky_messages = []
    
    for message in messages:
        score, categories = calculate_message_risk_score(message)
        
        if score >= min_score:
            risky_messages.append({
                'message': message,
                'score': score,
                'risk_level': classify_risk(score),
                'categories': categories
            })
    
    return risky_messages


# ตัวอย่างที่ 3: Detect และจัดกลุ่มตาม risk level
def detect_and_group_by_risk(messages: list) -> dict:
    """
    ตรวจสอบและจัดกลุ่มข้อความตามระดับความเสี่ยง
    
    Returns:
        dict ที่มี key เป็น risk level และ value เป็น list ของข้อความ
    """
    grouped = {
        'HIGH_RISK': [],
        'WARNING': [],
        'BE CAUTIOUS': [],
        'SAFE': []
    }
    
    for message in messages:
        score, categories = calculate_message_risk_score(message)
        risk_level = classify_risk(score)
        
        grouped[risk_level].append({
            'message': message,
            'score': score,
            'categories': categories
        })
    
    return grouped


# ตัวอย่างการใช้งาน
if __name__ == "__main__":
    # ข้อความทดสอบ
    test_messages = [
        "คุณชนะรางวัล 100,000 บาท! กดลิงค์นี้เลย: http://scam.com",
        "สวัสดีครับ วันนี้ทำงานอย่างไรบ้าง",
        "ด่วน! บัญชีของคุณจะถูกระงับ โปรดยืนยัน OTP: 123456",
        "เจอกันพรุ่งนี้นะ",
        "แจก iPhone 15 ฟรี! จำนวนจำกัด คลิกเลย www.free-iphone.com"
    ]
    
    print("=" * 80)
    print("ตัวอย่างที่ 1: Detect ทุกข้อความ")
    print("=" * 80)
    all_results = detect_multiple_messages(test_messages)
    for result in all_results:
        print(f"\nข้อความ: {result['message']}")
        print(f"คะแนน: {result['score']}")
        print(f"ระดับความเสี่ยง: {result['risk_level']}")
        print(f"หมวดหมู่: {result['categories']}")
    
    print("\n" + "=" * 80)
    print("ตัวอย่างที่ 2: เก็บเฉพาะข้อความที่มีความเสี่ยง (score >= 40)")
    print("=" * 80)
    risky_results = detect_and_filter_risky(test_messages, min_score=40)
    for result in risky_results:
        print(f"\n⚠️ ข้อความ: {result['message']}")
        print(f"   คะแนน: {result['score']}")
        print(f"   ระดับ: {result['risk_level']}")
    
    print("\n" + "=" * 80)
    print("ตัวอย่างที่ 3: จัดกลุ่มตามระดับความเสี่ยง")
    print("=" * 80)
    grouped_results = detect_and_group_by_risk(test_messages)
    for risk_level, items in grouped_results.items():
        print(f"\n📊 {risk_level}: {len(items)} ข้อความ")
        for item in items:
            print(f"   - {item['message'][:50]}... (score: {item['score']})")
    
    print("\n" + "=" * 80)
    print("ตัวอย่างที่ 4: ใช้ตัวแปร RISKY_MESSAGES เก็บข้อความที่มีความเสี่ยง")
    print("=" * 80)
    
    # ล้างข้อมูลเก่า
    clear_risky_messages()
    
    # ตรวจสอบแต่ละข้อความและเก็บลง RISKY_MESSAGES ถ้ามีความเสี่ยง
    print("\n📝 กำลังตรวจสอบและเก็บข้อความที่มีความเสี่ยง...")
    for msg in test_messages:
        result = add_risky_message(msg)
        if result:
            print(f"   ⚠️ เจอข้อความมีความเสี่ยง: {msg[:40]}... (score: {result['score']})")
        else:
            print(f"   ✓ ปลอดภัย: {msg[:40]}...")
    
    # แสดงจำนวนข้อความที่มีความเสี่ยง
    print(f"\n📊 จำนวนข้อความที่มีความเสี่ยง: {count_risky_messages()} ข้อความ")
    
    # แสดงข้อความที่มีความเสี่ยงทั้งหมดจากตัวแปร RISKY_MESSAGES
    print("\n🚨 รายการข้อความที่มีความเสี่ยง (จากตัวแปร RISKY_MESSAGES):")
    for msg in get_risky_messages():
        print(f"\n   ข้อความ: {msg['message']}")
        print(f"   คะแนน: {msg['score']}")
        print(f"   ระดับ: {msg['risk_level']}")
        print(f"   หมวดหมู่: {msg['categories']}")
    
    print("\n" + "=" * 80)
    print("💡 วิธีใช้ตัวแปร RISKY_MESSAGES:")
    print("=" * 80)
    print("1. add_risky_message(message)       - เพิ่มข้อความ (จะเก็บถ้ามีความเสี่ยง)")
    print("2. get_risky_messages()             - ดึงข้อความที่มีความเสี่ยงทั้งหมด")
    print("3. count_risky_messages()           - นับจำนวนข้อความที่มีความเสี่ยง")
    print("4. clear_risky_messages()           - ล้างข้อมูล")
    print("=" * 80)

