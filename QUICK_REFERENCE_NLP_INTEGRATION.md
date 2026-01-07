# Quick Reference: Extension NLP Integration

## TL;DR

The extension's popup now displays risk scores calculated by the NLP module using:
- **Category weights** from `NLP/scam_keywords.py` (10-30 points per category)
- **Regex pattern weights** from `NLP/_regex.py` (10-25 points per pattern)  
- **Bonus mechanisms** for repetition and escalation
- **Visual weight indicators** (🔴 critical → 🟢 low)

## File Changes

### Main Change: `extension/popup.js`

**Added three weight mappings:**

```javascript
// Line 111-122: Category weights
const CATEGORY_WEIGHTS = {
  "Promotional Bait": 30,    // Highest
  "Identity Threat": 25,     // Very high
  "OTP Request": 25,         // Very high
  "Authority": 20,           // High
  "Financial Pressure": 20,  // High
  "Delivery Scams": 20,      // High
  "Link Requests": 15,       // Medium
  "Urgency": 10              // Lower
};

// Line 124-131: Regex weights
const REGEX_WEIGHTS = {
  "Suspicious URL": 20,
  "Money Mentions": 10,
  "Time Pressure": 10,
  "OTP Request": 25
};

// Line 140-151: Weight indicator function
const getWeightIndicator = (category) => {
  let weight = CATEGORY_WEIGHTS[category] || REGEX_WEIGHTS[category] || 0;
  if (weight >= 30) return "🔴";  // Critical
  if (weight >= 25) return "🔴";  // Very high
  if (weight >= 20) return "🟠";  // High
  if (weight >= 15) return "🟡";  // Medium
  if (weight >= 10) return "🟡";  // Medium-low
  return "🟢";                     // Low
};
```

**Updated category display (Line 225-232):**

```javascript
// OLD:
categoryName.textContent = categoryData.name;

// NEW:
const weightIndicator = getWeightIndicator(categoryData.name);
let weight = CATEGORY_WEIGHTS[categoryData.name];
if (weight === undefined) {
  weight = REGEX_WEIGHTS[categoryData.name] || 0;
}
categoryName.textContent = `${weightIndicator} ${categoryData.name} (Weight: ${weight})`;
```

## Weight Hierarchy

```
Highest  🔴 Promotional Bait (30) - Most deceptive
         🔴 Identity Threat (25) - Account compromise
         🔴 OTP Request (25) - Account takeover
         🟠 Authority (20) - Impersonation
         🟠 Financial Pressure (20) - Loss of money
         🟠 Delivery Scams (20) - Fraud
         🟡 Link Requests (15) - Requires click
Lowest   🟡 Urgency (10) - Time pressure tactic
```

## How Risk Scores Work

### Single Message Example:
```
"ได้รับรางวัล 1,000 บาท! กดที่ http://prize.xyz"

Points breakdown:
  ├─ Promotional Bait (keyword) = 30
  ├─ Money pattern (บาท) = 10
  ├─ Suspicious URL (http://) = 20
  ├─ Identity Threat (implied) = 0
  └─ Multiple categories bonus = +20
  
Total: 30 + 10 + 20 + 20 = 80 → 🔴 High Risk
```

### Chat Example (Multiple Messages):
```
Message 1: "ได้รับรางวัล" = 30 (Promotional)
Message 2: "โปรโมชั่นพิเศษ" = 30 (Promotional)
Message 3: "รับเงินคืน 500 บาท" = 40 (Promotional + Money)

Subtotal: 30 + 30 + 40 = 100
Repetition Bonus (Promotional detected 3 times): +15
Escalation Bonus (3+ unique categories): +20
Final: min(100 + 15 + 20, 100) = 100 → 🔴 High Risk
```

## Integration Points

### Flow:
1. **Backend (app.py)** uses `NLP.risk_score_chat.analyze_chat()`
2. Returns JSON with `risk_score`, `flags`, `detected_categories`
3. **Frontend (popup.js)** displays using `CATEGORY_WEIGHTS` and `REGEX_WEIGHTS`
4. Categories show with visual weight indicators

### Data Flow:
```
NLP Module (weights) 
    ↓
Flask Backend (calculate score)
    ↓
REST API JSON response
    ↓
Popup JS (display with visual weights)
```

## Testing

Run the test suite:
```bash
python NLP/test_nlp_integration_weights.py
```

Expected output:
```
✅ test_category_weights - PASSED
✅ test_regex_weights - PASSED
✅ test_multiple_categories_bonus - PASSED
✅ test_chat_repetition_bonus - PASSED
✅ test_chat_escalation_bonus - PASSED
✅ test_risk_classification - PASSED
✅ test_popup_display_integration - PASSED
```

## Where to Find Things

| Item | File | Lines |
|------|------|-------|
| Category weights | `popup.js` | 111-122 |
| Regex weights | `popup.js` | 124-131 |
| Weight indicator function | `popup.js` | 140-151 |
| Category display | `popup.js` | 225-232 |
| Backend scoring | `app.py` | N/A (already done) |
| NLP weights source | `NLP/scam_keywords.py` | 1-125 |
| Regex patterns source | `NLP/_regex.py` | 1-50 |
| Integration tests | `NLP/test_nlp_integration_weights.py` | 1-280 |
| Documentation | `EXTENSION_NLP_INTEGRATION.md` | Full guide |
| Examples | `EXTENSION_SCORING_EXAMPLES.md` | 6 examples |

## Common Tasks

### Update a Category Weight:
1. Edit `NLP/scam_keywords.py` - change the weight value
2. Update `popup.js` line 111-122 - `CATEGORY_WEIGHTS`
3. Run tests to verify

### Add a New Regex Pattern:
1. Add regex to `NLP/_regex.py` - `REGEX` dict
2. Add weight to `NLP/_regex.py` - `REGEX_WEIGHT` dict
3. Update `popup.js` line 124-131 - `REGEX_WEIGHTS`
4. Update `risk_score_message.py` - add pattern detection
5. Run tests to verify

### Check Scoring Logic:
1. Look at `NLP/risk_score_message.py` - single message scoring
2. Look at `NLP/risk_score_chat.py` - chat-level bonuses
3. Look at `extension/app.py` - backend integration

## Key Constants

### Risk Level Thresholds:
```javascript
0: "Safe" 🟢
1-40: "Be cautious" 🟡
41-70: "Warning" 🟠
71-100: "High Risk" 🔴
```

### Bonus Points:
```
Multiple categories (same message):
  2 categories = +10
  3+ categories = +20

Repeated categories (across messages):
  2 occurrences = +8
  3+ occurrences = +15

Escalation (unique categories across messages):
  2 unique = +10
  3+ unique = +20
```

### Weight Ranges:
```
Categories: 10-30 points
Regex: 10-25 points
Bonuses: 8-20 points
Maximum score: 100 (capped)
```

## Visual Indicators

```
🔴 Critical/Very High   (25-30 points)
🟠 High                 (20-24 points)
🟡 Medium/Medium-Low    (10-19 points)
🟢 Low                  (< 10 points)
```

## Debugging

### If scores seem wrong:
1. Check `NLP/scam_keywords.py` - are weights correct?
2. Check `NLP/_regex.py` - are patterns matching?
3. Run `test_nlp_integration_weights.py` - all tests passing?
4. Check `extension/app.py` - is NLP pipeline being called?
5. Check browser console - any JS errors?

### If popup display is wrong:
1. Verify `CATEGORY_WEIGHTS` and `REGEX_WEIGHTS` match backend
2. Check `getWeightIndicator()` logic
3. Verify category display formatting (line 225-232)
4. Check CSS for style issues

## Recap

✅ Backend (app.py) already uses NLP weights
✅ Frontend (popup.js) now displays them visually
✅ Categories show with weight indicators (🔴🟠🟡🟢)
✅ All tests pass
✅ Documentation complete
