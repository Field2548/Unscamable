# Extension Risk Score Integration - NLP Module

## Summary of Changes

This document details the integration of the NLP module's sophisticated risk scoring algorithm into the Chrome extension's popup display. The extension now uses the same weighted risk calculation logic that the NLP module provides, ensuring accurate and consistent threat assessment.

## What Changed

### 1. **Backend (app.py) - Already Integrated ✅**

The Flask backend (`extension/app.py`) was already correctly using the NLP module:

```python
from NLP.chat_extractor import extract_chat_messages
from NLP.chat_grouper import group_chat_messages
from NLP.risk_score_chat import analyze_chat, CATEGORY_LABELS
from NLP.risk_score_message import calculate_message_risk_score
```

**Key functions used:**
- `calculate_message_risk_score()` - Applies category weights and regex patterns to individual messages
- `analyze_chat()` - Aggregates message scores with bonuses for repetition and escalation

### 2. **Frontend (popup.js) - Enhanced Display ✅**

Updated `extension/popup.js` to properly display NLP-calculated risk scores with visual weight indicators.

#### Key additions:

**a) Category Weights Mapping** - Reflects the weights from `NLP/scam_keywords.py`:
```javascript
const CATEGORY_WEIGHTS = {
  "Promotional Bait": 30,       // Highest
  "Identity Threat": 25,         // Very high
  "OTP Request": 25,             // Very high
  "Authority": 20,               // High
  "Financial Pressure": 20,      // High
  "Delivery Scams": 20,          // High
  "Link Requests": 15,           // Medium
  "Urgency": 10                  // Lower
};
```

**b) Regex Pattern Weights** - Reflects the weights from `NLP/_regex.py`:
```javascript
const REGEX_WEIGHTS = {
  "Suspicious URL": 20,          // URL pattern
  "Money Mentions": 10,          // Money pattern
  "Time Pressure": 10,           // Time pressure pattern
  "OTP Request": 25              // OTP pattern
};
```

**c) Visual Weight Indicators** - Shows the relative risk of each detected category:
```javascript
const getWeightIndicator = (category) => {
  const weight = CATEGORY_WEIGHTS[category] || REGEX_WEIGHTS[category] || 0;
  if (weight >= 30) return "🔴"; // Critical
  if (weight >= 25) return "🔴"; // Very High
  if (weight >= 20) return "🟠"; // High
  if (weight >= 15) return "🟡"; // Medium
  if (weight >= 10) return "🟡"; // Medium-Low
  return "🟢";                    // Lower
};
```

**d) Enhanced Category Display** - Categories now show both the weight indicator and numerical weight value:
```
🔴 Promotional Bait (Weight: 30)
  → "ได้รับรางวัล iPhone ใหม่"
🔴 Identity Threat (Weight: 25)
  → "บัญชีของคุณถูกแฮก"
🟠 Authority (Weight: 20)
  → "ตำรวจแจ้งคุณมีคดี"
```

## How It Works

### Risk Score Calculation Flow:

1. **User enters a page with text** → Content script extracts messages
2. **Backend processes text** via Flask `/analyze` endpoint
3. **NLP Pipeline applies weights:**
   - Category keyword matching → Add category weight (10-30 points each)
   - Regex pattern detection → Add regex weight (10-25 points each)
   - Multiple categories bonus → +10 or +20 points
   - Repetition bonus → +8 or +15 per repeated category
   - Escalation bonus → +10 or +20 for multiple unique categories
   - Cap final score at 100
4. **Risk classification:**
   - 0 points = Safe
   - 1-40 points = Be cautious
   - 41-70 points = Warning
   - 71-100 points = High Risk
5. **Popup displays:**
   - Overall risk score
   - Risk level with color-coded background
   - Detected categories with weight indicators
   - Keyword snippets for each category

## Category Weights Hierarchy

From `NLP/scam_keywords.py`:

| Category | Weight | Type | Risk Level |
|----------|--------|------|-----------|
| Promotional Bait | 30 | Content | 🔴 Critical |
| Identity Threat | 25 | Direct threat | 🔴 Very High |
| OTP Request | 25 | Pattern | 🔴 Very High |
| Authority | 20 | Impersonation | 🟠 High |
| Financial Pressure | 20 | Content | 🟠 High |
| Delivery Scams | 20 | Content | 🟠 High |
| Link Requests | 15 | Content | 🟡 Medium |
| Urgency | 10 | Tactic | 🟡 Medium-Low |

## Regex Pattern Weights

From `NLP/_regex.py`:

| Pattern | Weight | Examples |
|---------|--------|----------|
| OTP Detection | 25 | "OTP", "รหัส OTP" |
| Suspicious URL | 20 | "http://", "www.", "bit.ly", ".xyz", ".top" |
| Money Mentions | 10 | "1,000 บาท", "500บาท" |
| Time Pressure | 10 | "2 ชั่วโมง", "3 วัน" |

## Bonus Mechanisms

### Repetition Bonus
When the same category appears multiple times in a chat:
- **2 occurrences:** +8 points
- **3+ occurrences:** +15 points each

### Escalation Bonus
When multiple unique manipulation techniques are detected:
- **2 unique categories:** +10 points
- **3+ unique categories:** +20 points

### Multiple Category Bonus
Within a single message:
- **2 categories:** +10 points
- **3+ categories:** +20 points

## Files Modified

### 1. `extension/popup.js`
- Added `CATEGORY_WEIGHTS` mapping
- Added `REGEX_WEIGHTS` mapping
- Enhanced `getWeightIndicator()` function
- Updated category display to show weight indicators and values
- Category names now display as: `🔴 Category Name (Weight: 25)`

### 2. `NLP/test_nlp_integration_weights.py` (New)
Comprehensive test suite verifying:
- ✅ Category weight application
- ✅ Regex pattern weight application
- ✅ Multiple category bonuses
- ✅ Chat repetition bonuses
- ✅ Chat escalation bonuses
- ✅ Risk classification accuracy
- ✅ End-to-end popup display integration

**All tests passed successfully!** ✅

## Example Risk Score Breakdown

### Input Message:
"ได้รับรางวัล 1,000,000 บาท! ยืนยันตัวตนที่ http://prize.xyz"

### Scoring:
| Component | Weight | Points |
|-----------|--------|--------|
| Promotional Bait keyword match | 30 | +30 |
| Money pattern (บาท) | 10 | +10 |
| Suspicious URL pattern | 20 | +20 |
| Identity Threat keyword match | 25 | +25 |
| Multiple categories bonus (4 categories) | - | +20 |
| **Total Score** | - | **95** |

### Result:
- **Risk Level:** 🔴 **High Risk**
- **Score:** 95/100
- **Detected Categories:**
  - 🔴 Promotional Bait (Weight: 30)
  - 🔴 Identity Threat (Weight: 25)
  - 🟠 Authority (Weight: 20)
  - 🟡 Money Mentions (Weight: 10)

## Testing

Run the integration test to verify all weights are applied correctly:

```bash
python NLP/test_nlp_integration_weights.py
```

Expected output:
```
============================================================
✅ All tests passed!
The extension popup is now using NLP weights correctly:
  • Category weights from scam_keywords.py
  • Regex pattern weights from _regex.py
  • Repetition bonuses for repeated categories
  • Escalation bonuses for multiple unique categories
============================================================
```

## Benefits

1. **Accurate Threat Assessment:** Uses sophisticated NLP-based weighting instead of simple pattern matching
2. **Transparent Risk Indicators:** Users see exactly which factors contribute to the risk score
3. **Consistent Logic:** Same risk calculation across all components (backend, frontend, tests)
4. **Visual Priority:** Category weights are visually represented (🔴 = highest risk, 🟢 = lowest)
5. **Comprehensive Scoring:** Combines keyword detection, regex patterns, bonuses, and escalation logic

## Architecture

```
User Input (Chat/Message)
    ↓
Chrome Extension Content Script
    ↓
Flask Backend (app.py)
    ↓
NLP Pipeline:
  ├─ Message Extraction
  ├─ Message Grouping
  ├─ Risk Score Calculation (with weights)
  └─ Chat Analysis (with bonuses)
    ↓
Risk Score + Categories + Flags
    ↓
Popup Display (popup.js)
    ├─ Risk Score (0-100)
    ├─ Risk Level (Safe/Cautious/Warning/High Risk)
    ├─ Categories with Weight Indicators
    └─ Keyword Snippets
```

## Conclusion

The extension now uses the full power of the NLP module's weighted risk scoring system. Users can see exactly why messages are flagged as risky, with visual indicators showing which threat categories are most dangerous (Promotional Bait at 30 points) versus less critical ones (Urgency at 10 points).
