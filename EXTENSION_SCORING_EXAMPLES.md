# Extension NLP Integration - Scoring Examples

This document shows practical examples of how the extension now uses NLP weights to calculate risk scores.

## Example 1: Simple Promotional Scam

**Message:** "ได้รับรางวัล iPhone ใหม่ 🎁"

### Score Calculation:
```
Category: Promotional Bait
  Detected Keywords: "ได้รับรางวัล", "iPhone ใหม่"
  Weight: 30 points
  
Total Score: 30
Risk Level: 🟡 Be cautious
```

### Popup Display:
```
Risk Score: 30/100
Status: Be cautious
──────────────────────
🔴 Promotional Bait (Weight: 30)
  → "ได้รับรางวัล iPhone ใหม่ 🎁"
```

---

## Example 2: Authority + Financial + Urgency

**Message:** "ตำรวจแจ้งว่าคุณมีคดีความ ต้องชำระค่าปรับ 5,000 บาท วันนี้เท่านั้น"

### Score Calculation:
```
Category: Authority
  Detected Keywords: "ตำรวจ", "คดีความ"
  Weight: 20 points

Category: Financial Pressure
  Detected Keywords: "ค่าปรับ", "5,000 บาท"
  Weight: 20 points

Regex Pattern: Money (บาท)
  Pattern: "\d+(,\d+)?\s*บาท"
  Weight: 10 points

Category: Urgency
  Detected Keywords: "วันนี้เท่านั้น"
  Weight: 10 points

Multiple Categories Bonus (4 detected):
  +20 points

Total Score: 20 + 20 + 10 + 10 + 20 = 80
Risk Level: 🔴 High Risk
```

### Popup Display:
```
Risk Score: 80/100
Status: High Risk
──────────────────────
🟠 Authority (Weight: 20)
  → "ตำรวจแจ้งว่าคุณมีคดีความ"

🟠 Financial Pressure (Weight: 20)
  → "ค่าปรับ 5,000 บาท"

🟡 Money Mentions (Weight: 10)
  → "5,000 บาท"

🟡 Urgency (Weight: 10)
  → "วันนี้เท่านั้น"
```

---

## Example 3: Chat with Repetition Bonus

**Multiple Messages:**
1. "ได้รับรางวัล iPhone ใหม่"
2. "โปรโมชั่นพิเศษ ฝาก100รับ200"
3. "รับเงินคืน 500 บาท ทันที"

### Score Calculation:

**Message 1:**
```
Category: Promotional Bait (word match)
  Weight: 30 points
```

**Message 2:**
```
Category: Promotional Bait (word match)
  Weight: 30 points
```

**Message 3:**
```
Category: Promotional Bait (word match)
  Weight: 30 points
Regex: Money Pattern
  Weight: 10 points
```

**Repetition Bonus:**
```
Promotional Bait detected 3 times
  Bonus: +15 points
```

**Final Calculation:**
```
Message 1: 30
Message 2: 30
Message 3: 40 (30 + 10 for money)
Subtotal: 100
Repetition Bonus: +15
Cap at 100: 100

Total Chat Score: 100
Risk Level: 🔴 High Risk
```

### Popup Display:
```
Risk Score: 100/100
Status: High Risk
──────────────────────
🔴 Promotional Bait (Weight: 30) [3 occurrences]
  → "ได้รับรางวัล iPhone ใหม่"
  → "โปรโมชั่นพิเศษ ฝาก100รับ200"
  → "รับเงินคืน"

🟡 Money Mentions (Weight: 10)
  → "500 บาท"

Repetition Bonus: Promotional Bait detected 3 times: +15 points
```

---

## Example 4: Multiple Unique Categories (Escalation Bonus)

**Messages:**
1. "ยืนยันตัวตนของคุณ"
2. "ได้รับรางวัล 10,000 บาท"
3. "ติดต่อเจ้าหน้าที่ตำรวจ"

### Score Calculation:

**Message 1:**
```
Category: Identity Threat
  Keywords: "ยืนยันตัวตน"
  Weight: 25 points
```

**Message 2:**
```
Category: Promotional Bait
  Keywords: "ได้รับรางวัล"
  Weight: 30 points
Regex: Money
  Weight: 10 points
```

**Message 3:**
```
Category: Authority
  Keywords: "เจ้าหน้าที่ตำรวจ"
  Weight: 20 points
```

**Escalation Bonus:**
```
Unique categories detected:
  1. Identity Threat
  2. Promotional Bait
  3. Authority
  
3 unique categories = +20 points escalation bonus
```

**Final Calculation:**
```
Message 1: 25
Message 2: 40 (30 + 10)
Message 3: 20
Subtotal: 85
Escalation Bonus: +20
Capped at 100

Total Chat Score: 100
Risk Level: 🔴 High Risk
```

### Popup Display:
```
Risk Score: 100/100
Status: High Risk
──────────────────────
🔴 Identity Threat (Weight: 25)
  → "ยืนยันตัวตนของคุณ"

🔴 Promotional Bait (Weight: 30)
  → "ได้รับรางวัล 10,000 บาท"

🟠 Authority (Weight: 20)
  → "ติดต่อเจ้าหน้าที่ตำรวจ"

🟡 Money Mentions (Weight: 10)
  → "10,000 บาท"

Escalation Bonus: Detected 3 unique threat categories: +20 points
```

---

## Example 5: OTP + Identity Threat (Highest Risk Indicators)

**Message:** "ส่งรหัส OTP ของคุณเพื่อยืนยันบัญชี ด่วน!"

### Score Calculation:
```
Regex Pattern: OTP Detection
  Pattern: "รหัส OTP"
  Weight: 25 points

Category: Identity Threat
  Keywords: "บัญชีของคุณ", "ยืนยัน"
  Weight: 25 points

Category: Urgency
  Keywords: "ด่วน"
  Weight: 10 points

Multiple Categories Bonus (3 detected):
  +20 points

Total Score: 25 + 25 + 10 + 20 = 80
Risk Level: 🔴 High Risk
```

### Popup Display:
```
Risk Score: 80/100
Status: High Risk
──────────────────────
🔴 OTP Request (Weight: 25)
  → "รหัส OTP"

🔴 Identity Threat (Weight: 25)
  → "บัญชีของคุณ"

🟡 Urgency (Weight: 10)
  → "ด่วน!"
```

---

## Example 6: Safe Message (No Red Flags)

**Message:** "สวัสดี เคยไปเที่ยวเชียงใหม่หรือ"

### Score Calculation:
```
No keyword matches: 0 points
No regex patterns: 0 points

Total Score: 0
Risk Level: 🟢 Safe
```

### Popup Display:
```
Risk Score: 0/100
Status: Safe
──────────────────────
✅ No suspicious factors detected
```

---

## Weight Distribution

### Why These Weights?

```
Promotional Bait (30) - Highest
  └─ Most common, hardest to detect, highly deceptive

Identity Threat (25) - Very High
  └─ Direct account compromise risk

OTP Request (25) - Very High
  └─ Highest impact if succeeded (account takeover)

Authority (20) - High
  └─ Effective impersonation tactic

Financial Pressure (20) - High
  └─ Creates urgency to pay

Delivery Scams (20) - High
  └─ Specific, targeted fraud

Link Requests (15) - Medium
  └─ Requires user click to succeed

Urgency (10) - Medium-Low
  └─ Common tactic but needs other factors
```

---

## Comparison: Old vs. New

### Old Approach (Before Integration)
- Simple keyword matching
- Equal weight to all categories
- No regex pattern detection
- No bonus mechanisms
- Less accurate risk assessment

### New Approach (With NLP Integration)
- Weighted category matching (10-30 points per category)
- Regex pattern detection (10-25 points per pattern)
- Repetition bonus (+8-15 points for repeated categories)
- Escalation bonus (+10-20 points for multiple categories)
- Multiple category bonus (+10-20 points within messages)
- Maximum 100-point scale with intelligent capping
- Accurate risk classification

### Example Improvement:
**Message:** "ได้รับรางวัล 1,000 บาท กดที่ http://prize.xyz ยืนยันตัวตนทันที"

**Old System:** 
- Keywords: Multiple matches = ~50 points (crude counting)

**New System:**
- Promotional Bait: 30
- Money Pattern: 10
- URL Pattern: 20
- Identity Threat: 25
- Urgency: 10
- Multiple Categories Bonus: +20
- **Total: 95 points** (Much more accurate!)

---

## How Users See This

When a user opens the extension popup, they now see:

1. **Visual Risk Indicator**: 🔴 (Red) for High Risk
2. **Score**: 95/100
3. **Risk Level**: High Risk
4. **Category Breakdown**: Each category shows:
   - Weight indicator (🔴/🟠/🟡/🟢)
   - Category name
   - Numerical weight (30, 25, 20, etc.)
   - Example keyword from the message

This provides **transparency** and **education** about why messages are dangerous!
