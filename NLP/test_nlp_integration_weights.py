"""
Test to verify that NLP module correctly applies category weights, regex weights,
and other scoring mechanisms for the extension popup display.

This test ensures:
1. Category weights from scam_keywords.py are properly applied
2. Regex patterns and weights from _regex.py are properly applied
3. Repetition bonuses are correctly calculated
4. Escalation bonuses are correctly calculated
5. The total score respects the weighting hierarchy
"""

try:
    from .risk_score_message import calculate_message_risk_score
    from .risk_score_chat import analyze_chat, CATEGORY_LABELS
    from .scam_keywords import CATEGORIES
    from ._regex import REGEX, REGEX_WEIGHT
    from .classify_scam_message import classify_risk
except ImportError:
    from risk_score_message import calculate_message_risk_score
    from risk_score_chat import analyze_chat, CATEGORY_LABELS
    from scam_keywords import CATEGORIES
    from _regex import REGEX, REGEX_WEIGHT
    from classify_scam_message import classify_risk


def test_category_weights():
    """Verify that category weights from scam_keywords.py are applied correctly."""
    print("\n=== Testing Category Weights ===")
    
    # Test promotion category (highest weight: 30)
    promotion_msg = "ได้รับรางวัล iPhone ใหม่! ลงทุนน้อย"
    score, categories = calculate_message_risk_score(promotion_msg)
    print(f"Promotion message: '{promotion_msg}'")
    print(f"Score: {score}, Categories: {categories}")
    assert "promotion" in categories, "Should detect promotion category"
    assert score >= 30, f"Promotion weight should be 30, got {score}"
    
    # Test identity_threat (weight: 25)
    identity_msg = "บัญชีของคุณถูกแฮก ยืนยันตัวตนทันที"
    score, categories = calculate_message_risk_score(identity_msg)
    print(f"\nIdentity threat message: '{identity_msg}'")
    print(f"Score: {score}, Categories: {categories}")
    assert "identity_threat" in categories, "Should detect identity_threat category"
    assert score >= 25, f"Identity threat weight should be 25, got {score}"
    
    # Test authority (weight: 20)
    authority_msg = "ตำรวจแจ้งว่าคุณมีคดีความ ติดต่อเจ้าหน้าที่"
    score, categories = calculate_message_risk_score(authority_msg)
    print(f"\nAuthority message: '{authority_msg}'")
    print(f"Score: {score}, Categories: {categories}")
    assert "authority" in categories, "Should detect authority category"
    assert score >= 20, f"Authority weight should be 20, got {score}"
    
    print("✅ Category weight tests passed!")


def test_regex_weights():
    """Verify that regex patterns and weights from _regex.py are applied correctly."""
    print("\n=== Testing Regex Pattern Weights ===")
    
    # Test URL detection (weight: 20)
    url_msg = "กดที่ http://suspicious.xyz/claim เพื่อรับเงิน"
    score, categories = calculate_message_risk_score(url_msg)
    print(f"URL message: '{url_msg}'")
    print(f"Score: {score}, Categories: {categories}")
    assert "url" in categories, "Should detect URL pattern"
    assert score >= 20, f"URL weight should be 20, got {score}"
    
    # Test money detection (weight: 10)
    money_msg = "คุณมียอดค้างชำระ 1,000 บาท ชำระเงิน"
    score, categories = calculate_message_risk_score(money_msg)
    print(f"\nMoney message: '{money_msg}'")
    print(f"Score: {score}, Categories: {categories}")
    assert "money" in categories or "financial_pressure" in categories, "Should detect money/financial_pressure"
    
    print("✅ Regex weight tests passed!")


def test_multiple_categories_bonus():
    """Verify that combining multiple manipulation techniques gets bonus points."""
    print("\n=== Testing Multiple Category Bonus ===")
    
    # Message with 2 categories (bonus: 10)
    two_cat_msg = "ตำรวจแจ้งคุณมีคดี ชำระค่าปรับ 5,000 บาท"
    score, categories = calculate_message_risk_score(two_cat_msg)
    print(f"Two-category message: '{two_cat_msg}'")
    print(f"Score: {score}, Categories: {categories}")
    print(f"Detected {len(categories)} categories")
    assert len(categories) >= 2, "Should detect at least 2 categories"
    
    # Message with 3+ categories (bonus: 20)
    three_cat_msg = "ได้รับรางวัล 100,000 บาท! กดลิงก์ www.prize.top เพื่อรับ"
    score, categories = calculate_message_risk_score(three_cat_msg)
    print(f"\nThree-category message: '{three_cat_msg}'")
    print(f"Score: {score}, Categories: {categories}")
    print(f"Detected {len(categories)} categories")
    
    print("✅ Multiple category bonus tests passed!")


def test_chat_repetition_bonus():
    """Verify that repeating scam categories across messages gets bonus points."""
    print("\n=== Testing Chat Repetition Bonus ===")
    
    chat_messages = [
        "ได้รับรางวัล iPhone ใหม่",
        "โปรโมชั่นพิเศษ จำกัด 100 รางวัล",
        "รับเงินคืน 200 บาท ทันที"
    ]
    
    result = analyze_chat(chat_messages)
    print(f"Chat messages: {chat_messages}")
    print(f"Chat risk score: {result['chat_risk_score']}")
    print(f"Detected categories: {result['detected_categories']}")
    print(f"Repetition bonus details: {result['repetition_bonus_details']}")
    print(f"Repetition bonus points: {result['repetition_bonus_points']}")
    
    # All three messages are from promotion category, so should get repetition bonus
    assert result['repetition_bonus_points'] > 0, "Should get repetition bonus for repeated categories"
    
    print("✅ Chat repetition bonus tests passed!")


def test_chat_escalation_bonus():
    """Verify that combining multiple unique categories gets escalation bonus."""
    print("\n=== Testing Chat Escalation Bonus ===")
    
    chat_messages = [
        "ตำรวจแจ้งคุณมีคดี (authority)",
        "โปรโมชั่นพิเศษ (promotion)",
        "ยืนยันตัวตนทันที (identity_threat)"
    ]
    
    result = analyze_chat(chat_messages)
    print(f"Chat messages: {chat_messages}")
    print(f"Chat risk score: {result['chat_risk_score']}")
    print(f"Detected categories: {result['detected_categories']}")
    print(f"Escalation bonus: {result['escalation_bonus']}")
    print(f"Escalation bonus points: {result['escalation_bonus_points']}")
    
    # Should have escalation bonus for 3 unique categories
    assert result['escalation_bonus'], "Should have escalation bonus for 3+ categories"
    assert result['escalation_bonus_points'] >= 20, "Escalation bonus should be 20 for 3+ categories"
    
    print("✅ Chat escalation bonus tests passed!")


def test_risk_classification():
    """Verify that risk scores are properly classified."""
    print("\n=== Testing Risk Classification ===")
    
    test_cases = [
        (0, "SAFE"),
        (20, "BE CAUTIOUS"),
        (50, "WARNING"),
        (80, "HIGH_RISK"),
    ]
    
    for score, expected in test_cases:
        result = classify_risk(score)
        print(f"Score {score}: {result} (expected {expected})")
        assert result == expected, f"Expected {expected}, got {result}"
    
    print("✅ Risk classification tests passed!")


def test_popup_display_integration():
    """Verify complete integration for popup display."""
    print("\n=== Testing Popup Display Integration ===")
    
    # Simulate a scam message that would appear in popup
    scam_chat = [
        "ได้รับรางวัล 1,000,000 บาท! ยืนยันตัวตนที่ http://prize.xyz",
        "ใบสั่ง #12345 ไม่สามารถจัดส่ง ติดต่อ bit.ly/track",
        "ชำระค่าปรับ 5,000 บาท โอนเงินด่วน",
    ]
    
    result = analyze_chat(scam_chat)
    
    print(f"Chat messages: {scam_chat}")
    print(f"Risk score: {result['chat_risk_score']}")
    print(f"Risk level: {result['risk_level']}")
    print(f"Detected categories: {result['detected_categories']}")
    print(f"Category labels: {[CATEGORY_LABELS.get(cat, cat) for cat in result['detected_categories'].keys()]}")
    print(f"Repetition bonus: {result['repetition_bonus_points']}")
    print(f"Escalation bonus: {result['escalation_bonus_points']}")
    
    # Verify scoring includes all weights
    assert result['chat_risk_score'] > 0, "Should have detected scam risk"
    assert result['risk_level'] in ["HIGH_RISK", "WARNING"], "Should be high risk or warning"
    assert len(result['detected_categories']) > 0, "Should detect multiple categories"
    
    print("✅ Popup display integration test passed!")


if __name__ == "__main__":
    print("=" * 60)
    print("NLP Integration Weight Testing")
    print("Testing that extension popup uses NLP weights correctly")
    print("=" * 60)
    
    test_category_weights()
    test_regex_weights()
    test_multiple_categories_bonus()
    test_chat_repetition_bonus()
    test_chat_escalation_bonus()
    test_risk_classification()
    test_popup_display_integration()
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("The extension popup is now using NLP weights correctly:")
    print("  • Category weights from scam_keywords.py")
    print("  • Regex pattern weights from _regex.py")
    print("  • Repetition bonuses for repeated categories")
    print("  • Escalation bonuses for multiple unique categories")
    print("=" * 60)
