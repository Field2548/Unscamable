print("✅ LOADED: UPDATED OCR ENGINE V6 (NO ARGS)") 
import os
import re
from collections import abc
import cv2
import numpy as np

# --- 0. DISABLE NETWORK CHECK ---
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
from paddleocr import PaddleOCR

# --- 1. CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- 2. KNOWLEDGE BASE ---
THAI_BANKS = {
    "KBNK": ["kasikorn", "kbank", "กสิกร", "ก.ส.ก.", "kplus", "k+"],
    "SCB":  ["scb", "commercial", "ไทยพาณิชย์", "easy app", "แม่มณี"],
    "KTB":  ["krungthai", "ktb", "กรุงไทย", "next", "เป๋าตัง"],
    "BBL":  ["bangkok bank", "bbl", "กรุงเทพ", "bualuang"],
    "GSB":  ["gsb", "government savings", "ออมสิน", "mymo"],
    "TTB":  ["ttb", "tmb", "thanachart", "ทหารไทย", "ธนชาต"],
    "BAY":  ["krungsri", "bay", "กรุงศรี", "ayudhya", "kept"],
    "TRUE": ["truemoney", "true wallet", "ทรูมันนี่", "wallet"],
    "BAAC": ["baac", "ธ.ก.ส.", "เกษตร"],
}

SLIP_KEYWORDS = [
    "transfer successful", "โอนเงินสำเร็จ", "ทำรายการสำเร็จ", 
    "successful transaction", "e-slip", "receipt", 
    "จำนวนเงิน", "amount", "scan to verify", "ref no", "รหัสอ้างอิง"
]

NAME_PREFIXES = ["นาย", "นาง", "น.ส.", "ด.ช.", "ด.ญ.", "mr", "mrs", "miss", "ms"]

_OCR_INSTANCE = None
QUALITY_TARGET = 0.55
MAX_VARIANTS = 3

# --- 3. HELPER FUNCTIONS ---

def get_ocr_engine():
    global _OCR_INSTANCE
    if _OCR_INSTANCE is None:
        # V6: ABSOLUTELY MINIMAL ARGS. NO SHOW_LOG. NO USE_GPU.
        # This uses the default settings which work on all versions.
        _OCR_INSTANCE = PaddleOCR(lang='th')
    return _OCR_INSTANCE

def smart_resize(img):
    h, w = img.shape[:2]
    max_dim = max(h, w)
    if max_dim > 1800:
        scale = 1800 / max_dim
        return cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    elif max_dim < 800:
        return cv2.resize(img, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
    return img.copy()

def deskew_image(image, max_angle=12.0):
    if image is None: return image, 0.0
    if max(image.shape[:2]) > 1800: return image, 0.0
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        thresh = cv2.bitwise_not(thresh)
        coords = cv2.findNonZero(thresh)
        if coords is None: return image, 0.0
        rect = cv2.minAreaRect(coords)
        angle = rect[-1]
        if angle < -45: angle = 90 + angle
        if abs(angle) < 0.1 or abs(angle) > max_angle: return image, 0.0
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE), angle
    except:
        return image, 0.0

def _scale_with_limit(image, scale_factor, max_dim=2200):
    if image is None: return image
    h, w = image.shape[:2]
    longest = max(h, w)
    target_longest = longest * scale_factor
    if target_longest > max_dim and longest > 0:
        scale_factor = max_dim / float(longest)
    if scale_factor == 1.0: return image.copy()
    interpolation = cv2.INTER_CUBIC if scale_factor >= 1.0 else cv2.INTER_AREA
    return cv2.resize(image, None, fx=scale_factor, fy=scale_factor, interpolation=interpolation)

def crop_to_slip_contour(image):
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 50, 200)
        contours, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        h_img, w_img = image.shape[:2]
        total_area = h_img * w_img

        for c in contours[:3]:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(approx)
                contour_area = w * h
                if 0.15 < (contour_area / total_area) < 0.95:
                    if w > 200 and h > 200:
                        pad = 15
                        x = max(0, x - pad)
                        y = max(0, y - pad)
                        w = min(w_img - x, w + (pad*2))
                        h = min(h_img - y, h + (pad*2))
                        return image[y:y+h, x:x+w], True
        return image, False
    except:
        return image, False

def prepare_base_image(image):
    small_img = smart_resize(image)
    cropped_img, was_cropped = crop_to_slip_contour(small_img)
    _, angle = deskew_image(cropped_img)
    if abs(angle) < 0.5:
        return cropped_img
    corrected, _ = deskew_image(cropped_img)
    return corrected

def compute_image_stats(image):
    resized = smart_resize(image)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    h, w = image.shape[:2]
    return {
        'brightness': brightness,
        'contrast': contrast,
        'sharpness': sharpness,
        'longest': max(h, w),
        'shortest': min(h, w),
    }

def select_variant_sequence(stats):
    brightness = stats['brightness']
    sharpness = stats['sharpness']
    longest = stats['longest']
    contrast = stats['contrast']
    primary = 'balanced'
    if brightness < 95: primary = 'clahe'
    elif brightness > 185:
        primary = 'balanced'
        if contrast < 35: primary = 'clahe'
    elif sharpness < 45: primary = 'unsharp'
    elif longest < 1100: primary = 'upscaled'
    candidates = [primary]
    fallbacks = []
    if primary != 'balanced': fallbacks.append('balanced')
    if brightness < 110 and 'clahe' not in fallbacks and primary != 'clahe': fallbacks.append('clahe')
    if brightness > 170 and 'binary' not in fallbacks and primary != 'binary': fallbacks.append('binary')
    if sharpness < 55 and 'unsharp' not in fallbacks and primary != 'unsharp': fallbacks.append('unsharp')
    if longest < 1200 and 'upscaled' not in fallbacks and primary != 'upscaled': fallbacks.append('upscaled')
    sequence = []
    for label in candidates + fallbacks:
        if label not in sequence:
            sequence.append(label)
        if len(sequence) >= MAX_VARIANTS: break
    return sequence

def preprocess_variant(image, label):
    if label == 'balanced': 
        processed = balanced_preprocess(image)
        return processed[0] if isinstance(processed, tuple) else processed
    if label == 'upscaled': return upscaled_preprocess(image)
    if label == 'clahe': return clahe_preprocess(image)
    if label == 'unsharp': return unsharp_preprocess(image)
    if label == 'binary': return binary_preprocess(image)
    return image.copy()

def balanced_preprocess(image):
    img = _scale_with_limit(image, 1.5)
    img = cv2.GaussianBlur(img, (3, 3), 0)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    avg_brightness = float(np.mean(gray))
    if avg_brightness < 90:
        inverted = cv2.bitwise_not(img)
        return inverted, avg_brightness
    return img, avg_brightness

def upscaled_preprocess(image): return _scale_with_limit(image, 2.0)

def clahe_preprocess(image):
    img = smart_resize(image)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    merged = cv2.merge((cl, a, b))
    enhanced = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
    return cv2.GaussianBlur(enhanced, (3, 3), 0)

def unsharp_preprocess(image):
    img = smart_resize(image)
    blurred = cv2.GaussianBlur(img, (0, 0), 1.5)
    sharpened = cv2.addWeighted(img, 1.7, blurred, -0.7, 0)
    return sharpened

def binary_preprocess(image):
    img = smart_resize(image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 41, 9)
    return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

def merge_items_to_lines(items, y_threshold=15):
    if not items: return []
    sorted_items = sorted(items, key=lambda entry: entry['y'])
    lines = []
    current_group = [sorted_items[0]]
    for item in sorted_items[1:]:
        if abs(item['y'] - current_group[-1]['y']) < y_threshold:
            current_group.append(item)
            continue
        current_group.sort(key=lambda entry: entry['x'])
        merged_text = " ".join(entry['text'] for entry in current_group).strip()
        merged_score = float(np.mean([entry['score'] for entry in current_group])) if current_group else 0.0
        lines.append({'text': merged_text, 'score': merged_score, 'items': [dict(entry) for entry in current_group]})
        current_group = [item]
    current_group.sort(key=lambda entry: entry['x'])
    merged_text = " ".join(entry['text'] for entry in current_group).strip()
    merged_score = float(np.mean([entry['score'] for entry in current_group])) if current_group else 0.0
    lines.append({'text': merged_text, 'score': merged_score, 'items': [dict(entry) for entry in current_group]})
    return lines

def evaluate_variant_quality(items):
    if not items: return 0.0
    filtered = [item for item in items if item['score'] >= 0.2]
    candidate_items = filtered or items
    length_weighted = []
    low_confidence = 0
    for item in candidate_items:
        score = float(item['score'])
        text_length = max(len(item['text'].strip()), 1)
        length_weighted.append((score, text_length))
        if score < 0.45: low_confidence += 1
    weighted_total = sum(score * length for score, length in length_weighted)
    total_length = sum(length for _, length in length_weighted)
    weighted_mean = weighted_total / total_length if total_length else 0.0
    penalty = 0.12 * (low_confidence / len(candidate_items)) if candidate_items else 0.0
    return round(max(0.0, weighted_mean - penalty), 4)

def extract_bank(text_list):
    found_banks = set()
    full_text = " ".join(text_list).lower()
    for bank_code, keywords in THAI_BANKS.items():
        for keyword in keywords:
            if keyword in full_text: found_banks.add(bank_code.upper())
    return list(found_banks)

def extract_banks_with_scores(line_entries):
    bank_scores = {}
    for entry in line_entries:
        lower_text = entry['text'].lower()
        score = float(entry.get('score', 0.0))
        for bank_code, keywords in THAI_BANKS.items():
            if any(keyword in lower_text for keyword in keywords):
                bank_scores[bank_code.upper()] = max(bank_scores.get(bank_code.upper(), 0.0), score)
    return bank_scores

def extract_name(text_list):
    possible_names = []
    for line in text_list:
        clean_line = line.strip().lower()
        for prefix in NAME_PREFIXES:
            if clean_line.startswith(prefix):
                possible_names.append(clean_line)
                break
        if "ชื่อบัญชี" in clean_line or "account name" in clean_line:
            name_part = line.replace("ชื่อบัญชี", "").replace("account name", "").strip()
            if len(name_part) > 2:
                possible_names.append(clean_line.replace("ชื่อบัญชี", "").strip())
    return list(set(possible_names))

def clean_ocr_items(items):
    cleaned = []
    for item in items:
        text = re.sub(r'\s+[a-zA-Z]$', '', item['text'])
        if re.match(r'^[A-Z]{5,}$', text): continue
        text = text.strip()
        if not text: continue
        cleaned.append({**item, 'text': text})
    return cleaned

def dedupe_line_tokens(line): return line
def sanitize_line(line): return line.strip()

def score_accounts_from_lines(line_entries, accounts):
    account_scores = {}
    if not accounts: return account_scores
    for entry in line_entries:
        normalized = re.sub(r'[\s-]', '', entry['text'])
        score = float(entry.get('score', 0.0))
        for account in accounts:
            if account in normalized:
                account_scores[account] = max(account_scores.get(account, 0.0), score)
    return account_scores

def aggregate_text_confidence(target_text, line_entries):
    target_clean = sanitize_line(target_text).lower()
    if not target_clean: return 0.0
    matched_scores = []
    for entry in line_entries:
        entry_clean = sanitize_line(entry['text']).lower()
        if not entry_clean: continue
        if entry_clean in target_clean or target_clean in entry_clean:
            matched_scores.append(float(entry.get('score', 0.0)))
    return float(np.mean(matched_scores)) if matched_scores else 0.0

# --- SAFE PARSER ---
def _parse_predict_entry(entry):
    parsed = []
    if isinstance(entry, dict):
        text = entry.get('text') or entry.get('transcription') or entry.get('rec_text') or ""
        score = entry.get('score', 0.0)
        poly = entry.get('points') or entry.get('poly') or entry.get('dt_polys') or []
        if poly:
            pts_arr = np.array(poly, dtype=float)
            x = float(np.mean(pts_arr[:, 0]))
            y = float(np.mean(pts_arr[:, 1]))
            box = pts_arr.tolist()
        else:
            x, y = 0.0, 0.0
            box = []
        parsed.append({'text': text, 'score': float(score), 'x': x, 'y': y, 'box': box})
        return parsed

    if isinstance(entry, abc.Iterable) and not isinstance(entry, dict):
        if len(entry) == 1 and isinstance(entry[0], list): entry = entry[0]
        if len(entry) >= 2:
            box = entry[0]
            payload = entry[1]
            if not isinstance(box, list): return parsed
            text = ""
            score = 0.0
            if isinstance(payload, (list, tuple)):
                text = payload[0]
                if len(payload) > 1: score = payload[1]
            pts_arr = np.asarray(box, dtype=float)
            parsed.append({'text': text, 'score': float(score), 'y': float(np.mean(pts_arr[:, 1])), 'x': float(np.mean(pts_arr[:, 0])), 'box': box})
    return parsed

def _parse_predict_output(raw_output):
    items = []
    if not raw_output: return items
    if isinstance(raw_output, list) and len(raw_output) > 0:
        if isinstance(raw_output[0], list) and len(raw_output[0]) > 0:
            if isinstance(raw_output[0][0], (list, dict)):
                raw_output = raw_output[0]
    for entry in raw_output:
        items.extend(_parse_predict_entry(entry))
    return items

# --- MAIN EXECUTION ---
def run_ocr_scan(image_path=None):
    if image_path is None: target_path = DEFAULT_IMAGE
    else: target_path = image_path
    if not os.path.exists(target_path): return {"status": "error", "message": "File not found"}
    base_img = cv2.imread(target_path)
    if base_img is None: return {"status": "error", "message": "Unreadable image"}

    base_img = prepare_base_image(base_img)
    stats = compute_image_stats(base_img)
    if stats['brightness'] > 210 and stats['contrast'] < 25 and stats['sharpness'] < 160:
         return {"status": "empty", "message": "Frame blank", "data": {"raw_text": []}}

    variant_labels = select_variant_sequence(stats)
    ocr = get_ocr_engine()
    variant_results = []

    for i, label in enumerate(variant_labels):
        variant_img = preprocess_variant(base_img, label)
        try:
            # V6 FIX: REMOVE cls=True if that causes issues, or keep if supported
            # If "cls=True" fails next, delete it. But "show_log" was the main suspect.
            ocr_output = ocr.ocr(variant_img, cls=True) 
        except Exception: continue
        
        items = clean_ocr_items(_parse_predict_output(ocr_output))
        if not items: continue

        line_entries = merge_items_to_lines(items, y_threshold=15)
        if not line_entries: continue
        merged_lines = [entry['text'] for entry in line_entries]
        quality = evaluate_variant_quality(items)
        
        full_blob = " ".join(merged_lines).replace("-", "").replace(" ", "")
        account_candidates = re.findall(r'\d{10,12}', full_blob)
        bank_candidates = extract_bank(merged_lines)
        name_candidates = [dedupe_line_tokens(name) for name in extract_name(merged_lines)]
        is_slip = check_is_slip(merged_lines)

        variant_results.append({
            'label': label,
            'lines': merged_lines,
            'line_entries': line_entries,
            'quality': quality,
            'accounts': account_candidates,
            'banks': bank_candidates,
            'names': name_candidates,
            'is_slip': is_slip
        })
        if quality >= QUALITY_TARGET or (account_candidates and quality >= 0.45): break

    if not variant_results:
        return {"status": "empty", "message": "No text detected", "data": {"raw_text": []}}

    best_variant = max(variant_results, key=lambda v: v['quality'])
    line_entries = best_variant.get('line_entries', [])
    clean_lines = best_variant['lines']
    full_text_blob = " ".join(clean_lines).replace("-", "").replace(" ", "")
    account_numbers = re.findall(r'\d{10,12}', full_text_blob)
    account_numbers = [acct for acct in account_numbers if not (acct.startswith("25") and len(acct)==4)]
    bank_scores = extract_banks_with_scores(line_entries)
    banks = list(bank_scores.keys())
    names = best_variant.get('names') or []
    account_confidence = score_accounts_from_lines(line_entries, account_numbers)
    name_confidence = {name: aggregate_text_confidence(name, line_entries) for name in names}

    warning_flags = []
    if best_variant['is_slip'] and not account_numbers: warning_flags.append("DETECTED_SLIP_BUT_NO_ACCOUNT")
    if "TRUE" in banks: warning_flags.append("HIGH_RISK_WALLET_DETECTED")

    return {
        "status": "success",
        "data": {
            "banks": banks,
            "names": names,
            "accounts": account_numbers,
            "raw_text": clean_lines,
            "confidence": {
                "variant": best_variant['quality'],
                "banks": {code: round(score, 4) for code, score in bank_scores.items()},
                "accounts": {acct: round(account_confidence.get(acct, 0.0), 4) for acct in account_numbers},
                "names": {name: round(conf, 4) for name, conf in name_confidence.items()},
            },
            "is_slip": best_variant['is_slip'],
            "warning_flags": warning_flags
        }
    }

if __name__ == "__main__":
    print("Engine Ready.")