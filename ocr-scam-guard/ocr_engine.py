import os
import re
import cv2
import numpy as np

# --- 0. DISABLE NETWORK CHECK ---
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
from paddleocr import PaddleOCR

# --- 1. CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_IMAGE = os.path.join(BASE_DIR, 'test_slip.png') 

# --- 2. KNOWLEDGE BASE ---
THAI_BANKS = {
    "KBNK": ["kasikorn", "kbank", "กสิกร", "ก.ส.ก."],
    "SCB":  ["scb", "commercial", "ไทยพาณิชย์"],
    "KTB":  ["krungthai", "ktb", "กรุงไทย"],
    "BBL":  ["bangkok bank", "bbl", "กรุงเทพ"],
    "GSB":  ["gsb", "government savings", "ออมสิน"],
    "TTB":  ["ttb", "tmb", "thanachart", "ทหารไทย", "ธนชาต"],
    "BAY":  ["krungsri", "bay", "กรุงศรี", "ayudhya"],
}

NAME_PREFIXES = ["นาย", "นาง", "น.ส.", "ด.ช.", "ด.ญ.", "mr", "mrs", "miss", "ms"]
NAME_PREFIX_LOWER = {prefix.lower() for prefix in NAME_PREFIXES}

_OCR_INSTANCE = None
QUALITY_TARGET = 0.55
MAX_VARIANTS = 3


# --- 3. HELPER FUNCTIONS ---

def get_ocr_engine():
    global _OCR_INSTANCE
    if _OCR_INSTANCE is None:
        _OCR_INSTANCE = PaddleOCR(
            lang='th',
            use_angle_cls=False,
            text_det_thresh=0.1,
            text_det_unclip_ratio=2.0,
            text_det_limit_side_len=2000, # Reduced to 2000 for safety
        )
    return _OCR_INSTANCE


def smart_resize(img):
    """
    STRICT RESIZING:
    Ensures image never exceeds 1800px on the longest side.
    This prevents memory crashes on large images.
    """
    h, w = img.shape[:2]
    max_dim = max(h, w)
    
    # If image is huge (>1800), shrink it down
    if max_dim > 1800:
        scale = 1800 / max_dim
        return cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    
    # If image is tiny (<800), grow it slightly
    elif max_dim < 800:
        return cv2.resize(img, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
    
    return img.copy()


def deskew_image(image, max_angle=12.0):
    if image is None: return image, 0.0
    # Optimization: Skip deskew if image is large (too slow)
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
        rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return rotated, angle
    except:
        return image, 0.0

def _scale_with_limit(image, scale_factor, max_dim=2200):
    if image is None: return image
    h, w = image.shape[:2]
    longest = max(h, w)
    target_longest = longest * scale_factor
    if target_longest > max_dim and longest > 0:
        scale_factor = max_dim / float(longest)
    if scale_factor == 1.0:
        return image.copy()
    interpolation = cv2.INTER_CUBIC if scale_factor >= 1.0 else cv2.INTER_AREA
    return cv2.resize(image, None, fx=scale_factor, fy=scale_factor, interpolation=interpolation)


def prepare_base_image(image):
    small_img = smart_resize(image)
    _, angle = deskew_image(small_img)
    if abs(angle) < 0.5:
        return image
    corrected, _ = deskew_image(image)
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
        'height': h,
        'width': w,
        'longest': max(h, w),
        'shortest': min(h, w),
    }


def select_variant_sequence(stats):
    brightness = stats['brightness']
    sharpness = stats['sharpness']
    longest = stats['longest']
    contrast = stats['contrast']

    primary = 'balanced'
    if brightness < 95:
        primary = 'clahe'
    elif brightness > 185:
        primary = 'balanced'
        if contrast < 35:
            primary = 'clahe'
    elif sharpness < 45:
        primary = 'unsharp'
    elif longest < 1100:
        primary = 'upscaled'

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
        if len(sequence) >= MAX_VARIANTS:
            break

    return sequence


def preprocess_variant(image, label):
    if label == 'balanced':
        processed, _ = balanced_preprocess(image)
        return processed
    if label == 'upscaled':
        return upscaled_preprocess(image)
    if label == 'clahe':
        return clahe_preprocess(image)
    if label == 'unsharp':
        return unsharp_preprocess(image)
    if label == 'binary':
        return binary_preprocess(image)
    return image.copy()


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
        lines.append({
            'text': merged_text,
            'score': merged_score,
            'items': [dict(entry) for entry in current_group],
        })
        current_group = [item]

    current_group.sort(key=lambda entry: entry['x'])
    merged_text = " ".join(entry['text'] for entry in current_group).strip()
    merged_score = float(np.mean([entry['score'] for entry in current_group])) if current_group else 0.0
    lines.append({
        'text': merged_text,
        'score': merged_score,
        'items': [dict(entry) for entry in current_group],
    })

    return lines


def evaluate_variant_quality(items):
    if not items: return 0.0

    filtered = [item for item in items if item['score'] >= 0.2]
    candidate_items = filtered or items

    length_weighted = []
    low_confidence = 0

    for item in candidate_items:
        score = float(item['score'])
        score = max(0.0, min(1.0, score))
        text_length = max(len(item['text'].strip()), 1)
        length_weighted.append((score, text_length))
        if score < 0.45:
            low_confidence += 1

    weighted_total = sum(score * length for score, length in length_weighted)
    total_length = sum(length for _, length in length_weighted)
    weighted_mean = weighted_total / total_length if total_length else 0.0

    top_scores = sorted((score for score, _ in length_weighted), reverse=True)
    top_take = max(3, int(np.ceil(len(top_scores) * 0.3)))
    top_subset = top_scores[:top_take]
    top_mean = float(np.mean(top_subset)) if top_subset else 0.0

    penalty = 0.12 * (low_confidence / len(candidate_items)) if candidate_items else 0.0
    composite = (0.65 * weighted_mean) + (0.35 * top_mean) - penalty

    return round(max(0.0, composite), 4)


def balanced_preprocess(image):
    """Balanced: gentle 1.5x upscale plus mild blur for Thai scripts."""
    img = _scale_with_limit(image, 1.5)
    img = cv2.GaussianBlur(img, (3, 3), 0)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    avg_brightness = float(np.mean(gray))
    if avg_brightness < 90:
        inverted = cv2.bitwise_not(img)
        return inverted, avg_brightness
    return img, avg_brightness


def upscaled_preprocess(image):
    """Upscaled: 2x enlargement using bicubic interpolation for tiny text."""
    return _scale_with_limit(image, 2.0)


def clahe_preprocess(image):
    """CLAHE: boost local contrast to surface white text in colored bubbles."""
    img = smart_resize(image)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    merged = cv2.merge((cl, a, b))
    enhanced = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
    return cv2.GaussianBlur(enhanced, (3, 3), 0)


def unsharp_preprocess(image):
    """Unsharp Mask: sharpen soft edges to split merged characters."""
    img = smart_resize(image)
    blurred = cv2.GaussianBlur(img, (0, 0), 1.5)
    sharpened = cv2.addWeighted(img, 1.7, blurred, -0.7, 0)
    return sharpened


def binary_preprocess(image):
    """Binary: adaptive threshold for crisp digit extraction."""
    img = smart_resize(image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 41, 9)
    return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)


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
    business_keywords = ["co.", "ltd", "store", "shop", "limited", "company", "หจก", "บจก"]

    for i, line in enumerate(text_list):
        clean_line = line.strip().lower()
        is_name = False

        for prefix in NAME_PREFIXES:
            if not clean_line.startswith(prefix): continue
            
            # Logic to grab next line if prefix stands alone
            if len(clean_line) < len(prefix) + 2 and i + 1 < len(text_list):
                possible_names.append(f"{line} {text_list[i+1]}")
            else:
                possible_names.append(line)
            is_name = True
            break

        if is_name: continue

        if "ชื่อบัญชี" in clean_line or "account name" in clean_line:
            name_part = line.replace("ชื่อบัญชี", "").replace("account name", "").strip()
            if name_part: possible_names.append(name_part)
            continue

        for keyword in business_keywords:
            if keyword in clean_line:
                possible_names.append(line)
                break

    return possible_names

def clean_ocr_items(items):
    cleaned = []
    for item in items:
        text = re.sub(r'\s+[a-zA-Z]$', '', item['text'])
        if re.match(r'^[A-Z]{5,}$', text): continue
        text = text.strip()
        if not text: continue
        cleaned.append({**item, 'text': text})
    return cleaned

def dedupe_line_tokens(line):
    return line

def sanitize_line(line):
    return line.strip()


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

# --- 4. MAIN EXECUTION ---

def run_ocr_scan(image_path=None):
    if image_path is None: target_path = DEFAULT_IMAGE
    else: target_path = image_path

    if not os.path.exists(target_path):
        return {"status": "error", "message": "File not found"}

    # print(f"🔍 Scanning '{target_path}'...") # Optional: uncomment if you want logs

    base_img = cv2.imread(target_path)
    if base_img is None:
        return {"status": "error", "message": "Unreadable image"}

    base_img = prepare_base_image(base_img)
    stats = compute_image_stats(base_img)

    if stats['brightness'] > 210 and stats['contrast'] < 25 and stats['sharpness'] < 160:
        return {
            "status": "empty",
            "message": "Frame is high brightness with minimal contrast; treated as blank.",
            "data": {
                "banks": [],
                "names": [],
                "accounts": [],
                "raw_text": [],
                "confidence": {
                    "variant": 0.0,
                    "banks": {},
                    "accounts": {},
                    "names": {},
                }
            }
        }

    variant_labels = select_variant_sequence(stats)

    ocr = get_ocr_engine()
    variant_results = []

    # 2. Run OCR Loop with early exit once quality is acceptable
    total_variants = len(variant_labels)
    for i, label in enumerate(variant_labels):
        variant_img = preprocess_variant(base_img, label)
        print(f"   -> Processing variant {i+1}/{total_variants}: {label}...")

        try:
            ocr_output = ocr.predict(variant_img)
        except Exception as err:
            print(f"   ⚠️ OCR variant '{label}' failed: {err}")
            continue
        if not ocr_output: continue

        data = ocr_output[0]
        if not data: continue
        
        # Safe extraction
        texts_raw = data.get('rec_texts') if data.get('rec_texts') is not None else []
        scores_raw = data.get('rec_scores') if data.get('rec_scores') is not None else []
        boxes_raw = data.get('rec_polys') if data.get('rec_polys') is not None else (data.get('rec_boxes') if data.get('rec_boxes') is not None else [])

        items = []
        count = min(len(boxes_raw), len(texts_raw), len(scores_raw))
        
        for k in range(count):
            pts = np.asarray(boxes_raw[k], dtype=float)
            y_center = float(np.mean(pts[:, 1]))
            x_center = float(np.mean(pts[:, 0]))
            items.append({'box': pts.tolist(), 'text': texts_raw[k], 'score': float(scores_raw[k]), 'y': y_center, 'x': x_center})

        cleaned_items = clean_ocr_items(items)
        if not cleaned_items: continue

        line_entries = merge_items_to_lines(cleaned_items, y_threshold=15)
        if not line_entries: continue

        merged_lines = [entry['text'] for entry in line_entries]
        quality = evaluate_variant_quality(cleaned_items)
        full_blob = " ".join(merged_lines)
        clean_blob = full_blob.replace("-", "").replace(" ", "")
        account_candidates = re.findall(r'\d{10,12}', clean_blob)
        bank_candidates = extract_bank(merged_lines)
        name_candidates = [dedupe_line_tokens(name) for name in extract_name(merged_lines)]
        name_candidates = [name for name in name_candidates if name]

        variant_results.append({
            'label': label,
            'lines': merged_lines,
            'line_entries': line_entries,
            'quality': quality,
            'accounts': account_candidates,
            'banks': bank_candidates,
            'names': name_candidates,
        })

        has_accounts = bool(account_candidates)
        has_banks = bool(bank_candidates)
        if quality >= QUALITY_TARGET or (has_accounts and quality >= 0.45) or (has_banks and quality >= 0.5):
            break

    if not variant_results:
        return {
            "status": "empty",
            "message": "OCR returned no readable text across selected variants.",
            "data": {
                "banks": [],
                "names": [],
                "accounts": [],
                "raw_text": [],
                "confidence": {
                    "variant": 0.0,
                    "banks": {},
                    "accounts": {},
                    "names": {},
                }
            }
        }

    # 3. Pick Winner
    best_variant = max(variant_results, key=lambda v: v['quality'])
    
    line_entries = best_variant.get('line_entries', [])
    clean_lines = best_variant['lines']
    full_text_blob = " ".join(clean_lines)
    clean_text_blob = full_text_blob.replace("-", "").replace(" ", "")

    account_numbers = re.findall(r'\d{10,12}', clean_text_blob)
    bank_scores = extract_banks_with_scores(line_entries) if line_entries else {}
    banks = list(bank_scores.keys()) if bank_scores else best_variant.get('banks', [])
    names = best_variant.get('names') or [dedupe_line_tokens(name) for name in extract_name(clean_lines)]
    names = [name for name in names if name]

    account_confidence = score_accounts_from_lines(line_entries, account_numbers) if line_entries else {}
    name_confidence = {name: aggregate_text_confidence(name, line_entries) for name in names}

    confidence_payload = {
        "variant": best_variant['quality'],
        "banks": {code: round(score, 4) for code, score in bank_scores.items()},
        "accounts": {acct: round(account_confidence.get(acct, 0.0), 4) for acct in account_numbers},
        "names": {name: round(conf, 4) for name, conf in name_confidence.items()},
    }

    return {
        "status": "success",
        "data": {
            "banks": banks,
            "names": names,
            "accounts": account_numbers,
            "raw_text": clean_lines,
            "confidence": confidence_payload,
        }
    }

if __name__ == "__main__":
    result = run_ocr_scan('test_slip.png')
    print("\n" + "="*40)
    print("       🕵️ SCAM GUARD INTELLIGENCE 🕵️")
    print("="*40)
    if result['status'] == 'success':
        print(f"🏦 Bank: {result['data']['banks']}")
        print(f"👤 Name: {result['data']['names']}")
        print(f"🚨 Account: {result['data']['accounts']}")
        print("-" * 40)
        print("📜 RAW TEXT:")
        for line in result['data']['raw_text']:
            print(f"📄 {line}")