import os
import re
from difflib import SequenceMatcher

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


# --- 3. HELPER FUNCTIONS ---

def get_ocr_engine():
    global _OCR_INSTANCE
    if _OCR_INSTANCE is None:
        _OCR_INSTANCE = PaddleOCR(
            lang='th',
            use_textline_orientation=True,
            text_det_thresh=0.1,
            text_det_unclip_ratio=2.0,
            text_det_limit_side_len=3000,
        )
    return _OCR_INSTANCE


def upscale_image(img, scale=1.5):
    return cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)


def balanced_preprocess(image_input):
    """Gentle zoom + blur + optional invert for dark UIs."""
    if isinstance(image_input, str):
        img = cv2.imread(image_input)
    else:
        img = image_input.copy() if image_input is not None else None
    if img is None:
        return None, None

    img = upscale_image(img)
    img = cv2.GaussianBlur(img, (3, 3), 0)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    avg_brightness = float(np.mean(gray))

    if avg_brightness < 100:
        img = cv2.bitwise_not(img)

    return img, avg_brightness


def apply_clahe(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l_channel = clahe.apply(l_channel)
    merged = cv2.merge((l_channel, a_channel, b_channel))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)


def apply_unsharp_mask(img):
    gaussian = cv2.GaussianBlur(img, (0, 0), 3)
    return cv2.addWeighted(img, 1.5, gaussian, -0.5, 0)


def apply_adaptive_binary(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 41, 10)
    return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)


def generate_preprocess_variants(image):
    variants = []
    balanced_img, brightness = balanced_preprocess(image)
    if balanced_img is not None:
        variants.append(("balanced", balanced_img))

    upscaled = upscale_image(image)
    variants.append(("upscaled", upscaled))
    variants.append(("clahe", apply_clahe(upscaled)))
    variants.append(("unsharp", apply_unsharp_mask(upscaled)))
    variants.append(("binary", apply_adaptive_binary(upscaled)))

    return variants, brightness

def merge_lines(boxes, texts, y_threshold=15): 
    # Adjusted threshold for 1.5x scale
    if not boxes or not texts: return []
    lines = []
    for box, text in zip(boxes, texts):
        try:
            y_center = (box[0][1] + box[2][1]) / 2
            x_start = box[0][0]
        except:
            y_center = (box[1] + box[3]) / 2
            x_start = box[0]
        lines.append({'text': text, 'y': y_center, 'x': x_start})

    lines.sort(key=lambda k: k['y'])
    merged_lines = []
    if not lines: return []

    current_line = [lines[0]]
    for i in range(1, len(lines)):
        block = lines[i]
        if abs(block['y'] - current_line[-1]['y']) < y_threshold:
            current_line.append(block)
        else:
            current_line.sort(key=lambda k: k['x'])
            merged_lines.append(" ".join([item['text'] for item in current_line]))
            current_line = [block]

    current_line.sort(key=lambda k: k['x'])
    merged_lines.append(" ".join([item['text'] for item in current_line]))
    return merged_lines

def extract_bank(text_list):
    found_banks = set()
    full_text = " ".join(text_list).lower()
    for bank_code, keywords in THAI_BANKS.items():
        for keyword in keywords:
            if keyword in full_text: found_banks.add(bank_code.upper())
    return list(found_banks)

def extract_name(text_list):
    possible_names = []
    business_keywords = ["co.", "ltd", "store", "shop", "limited", "company", "หจก", "บจก"]

    for i, line in enumerate(text_list):
        clean_line = line.strip().lower()
        is_name = False

        for prefix in NAME_PREFIXES:
            if not clean_line.startswith(prefix):
                continue

            if len(clean_line) < len(prefix) + 2 and i + 1 < len(text_list):
                combined = normalize_name_text(f"{line} {text_list[i + 1]}")
                if combined:
                    possible_names.append(combined)
            else:
                cleaned = normalize_name_text(line)
                if cleaned:
                    possible_names.append(cleaned)
            is_name = True
            break

        if is_name:
            continue

        if "ชื่อบัญชี" in clean_line or "account name" in clean_line:
            name_part = line.replace("ชื่อบัญชี", "").replace("account name", "").strip()
            cleaned = normalize_name_text(name_part)
            if cleaned:
                possible_names.append(cleaned)
            continue

        for keyword in business_keywords:
            if keyword in clean_line:
                cleaned = normalize_name_text(line)
                if cleaned:
                    possible_names.append(cleaned)
                break

    return possible_names

def clean_ocr_items(items):
    cleaned = []
    for item in items:
        text = re.sub(r'\s+[a-zA-Z]$', '', item['text'])
        if re.match(r'^[A-Z]{5,}$', text):
            continue
        text = text.strip()
        if not text:
            continue
        cleaned.append({**item, 'text': text})
    return cleaned


def dedupe_line_tokens(line, threshold=0.9, window=2):
    tokens = line.split()
    if not tokens:
        return line

    cleaned_tokens = []
    for token in tokens:
        lowered = token.lower()
        is_duplicate = False
        for prev in cleaned_tokens[-window:]:
            if SequenceMatcher(None, lowered, prev.lower()).ratio() >= threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            cleaned_tokens.append(token)
    return " ".join(cleaned_tokens)


def has_mixed_scripts(token):
    has_thai = any(0x0E00 <= ord(ch) <= 0x0E7F for ch in token)
    has_latin = any('a' <= ch.lower() <= 'z' for ch in token if ch.isalpha())
    return has_thai and has_latin


def is_short_ascii_noise(token):
    if not token.isalpha():
        return False
    lowered = token.lower()
    if lowered in NAME_PREFIX_LOWER:
        return False
    if len(token) <= 3:
        upper_ratio = sum(1 for ch in token if ch.isupper()) / len(token)
        vowel_present = any(ch in "aeiou" for ch in lowered)
        if upper_ratio >= 0.6 and not vowel_present:
            return True
    return False


def sanitize_line(line, alnum_mix_max=8):
    cleaned_tokens = []
    prefix_seen = False
    seen_numeric = set()
    seen_lower = set()
    for token in line.split():
        trimmed = token.strip()
        if not trimmed:
            continue
        lowered = trimmed.lower()
        if lowered in NAME_PREFIX_LOWER:
            if prefix_seen:
                break
            prefix_seen = True
        if has_mixed_scripts(trimmed):
            continue
        if re.fullmatch(r"[-–—]+", trimmed):
            continue
        if trimmed.isdigit() and len(trimmed) == 1:
            continue
        if re.search(r"[A-Za-z]", trimmed) and re.search(r"\d", trimmed) and len(trimmed) <= alnum_mix_max:
            continue
        if is_short_ascii_noise(trimmed):
            continue
        if any(ch.isdigit() for ch in trimmed):
            if trimmed in seen_numeric:
                continue
            seen_numeric.add(trimmed)
        else:
            if lowered in seen_lower and len(trimmed) > 1:
                continue
            seen_lower.add(lowered)
        cleaned_tokens.append(trimmed)
    return " ".join(cleaned_tokens)


def normalize_name_text(text):
    tokens = []
    for raw_token in text.split():
        token = raw_token.strip()
        if not token:
            continue

        lowered = token.lower()
        if lowered in NAME_PREFIX_LOWER and tokens:
            break

        if any(ch.isdigit() for ch in token):
            continue
        if len(token) == 1 and re.match(r"[A-Za-zก-๙]", token):
            continue
        if has_mixed_scripts(token):
            break
        if not re.search(r"[A-Za-zก-๙]", token):
            continue

        if is_short_ascii_noise(token):
            continue

        tokens.append(token)

    return " ".join(tokens).strip()


def aggregate_variant_lines(variants, y_threshold=15):
    if not variants:
        return []

    position_map = {}
    for variant in variants:
        for item in variant['items']:
            key = (round(item['y'] / 12), round(item['x'] / 12))
            stored = position_map.get(key)
            if stored is None or item['score'] > stored['score']:
                position_map[key] = item

    if not position_map:
        return []

    chosen = sorted(position_map.values(), key=lambda it: (it['y'], it['x']))
    boxes = [item['box'] for item in chosen]
    texts = [item['text'] for item in chosen]
    return merge_lines(boxes, texts, y_threshold=y_threshold)

# --- 4. MAIN EXECUTION ---

def run_ocr_scan(image_path=None):
    if image_path is None: target_path = DEFAULT_IMAGE
    else: target_path = image_path

    if not os.path.exists(target_path):
        print(f"❌ Error: Cannot find '{target_path}'")
        return {"status": "error", "message": "File not found"}

    print(f"🔍 Scanning '{target_path}'...")

    base_img = cv2.imread(target_path)
    if base_img is None:
        print("❌ Error: Unable to read image data.")
        return {"status": "error", "message": "Unreadable image"}

    variants, brightness = generate_preprocess_variants(base_img)
    if brightness is not None:
        if brightness < 100:
            print(f"   🌑 Dark Mode Detected ({brightness:.0f}) -> Inverting & smoothing.")
        else:
            print(f"   ☀️ Light Mode Detected ({brightness:.0f}) -> Smoothing & gentle zoom.")

    ocr = get_ocr_engine()

    variant_results = []
    for label, variant_img in variants:
        ocr_output = ocr.predict(variant_img)
        if not ocr_output:
            continue

        data = ocr_output[0]
        texts_raw = data.get('rec_texts') or []
        scores_raw = data.get('rec_scores') or []
        boxes_raw = data.get('rec_polys') or data.get('rec_boxes') or []

        items = []
        for box, text, score in zip(boxes_raw, texts_raw, scores_raw):
            if text is None:
                continue
            pts = np.asarray(box, dtype=float)
            y_center = float(np.mean(pts[:, 1]))
            x_center = float(np.mean(pts[:, 0]))
            items.append({
                'box': pts.tolist(),
                'text': text,
                'score': float(score),
                'y': y_center,
                'x': x_center,
            })

        cleaned_items = clean_ocr_items(items)
        if not cleaned_items:
            continue

        boxes = [item['box'] for item in cleaned_items]
        texts = [item['text'] for item in cleaned_items]
        merged_lines = merge_lines(boxes, texts, y_threshold=15)

        avg_score = sum(item['score'] for item in cleaned_items) / len(cleaned_items)
        quality = avg_score + len(merged_lines) * 0.01

        variant_results.append({
            'label': label,
            'lines': merged_lines,
            'items': cleaned_items,
            'quality': quality,
        })

    if not variant_results:
        print("❌ No text found.")
        return {"status": "empty", "data": {}}

    best_variant = max(variant_results, key=lambda v: v['quality'])
    print(f"   ✅ Using '{best_variant['label']}' preprocessing (confidence score {best_variant['quality']:.2f}).")

    combined_lines = aggregate_variant_lines(variant_results)
    clean_lines = best_variant['lines'] if best_variant['lines'] else []
    if combined_lines and len(combined_lines) <= len(clean_lines) + 3:
        clean_lines = combined_lines
    clean_lines = [sanitize_line(dedupe_line_tokens(line)) for line in clean_lines]
    clean_lines = [line for line in clean_lines if line]
    full_text_blob = " ".join(clean_lines)
    clean_text_blob = full_text_blob.replace("-", "").replace(" ", "")

    account_numbers = re.findall(r'\d{10,12}', clean_text_blob)
    banks = extract_bank(clean_lines)
    names = [dedupe_line_tokens(name, threshold=0.85) for name in extract_name(clean_lines)]
    names = [name for name in names if name]

    # 5. Final Report
    print("\n" + "="*40)
    print("       🕵️ SCAM GUARD INTELLIGENCE 🕵️")
    print("="*40)
    
    has_relevant_data = False

    if banks:
        print(f"🏦 Bank Mentioned:   {banks}")
        has_relevant_data = True
    if names:
        print(f"👤 Name Found:       {names}")
        has_relevant_data = True
    if account_numbers:
        print(f"🚨 ACCOUNT FOUND:    {account_numbers}")
        print("   (⚠️ High Risk: Send to Blacklist Check)")
        has_relevant_data = True
    
    if not has_relevant_data:
        print("ℹ️  No banking details detected.")

    print("-" * 40)
    print("📜 SCANNED TEXT:")
    for line in clean_lines:
        print(f"📄 {line}")
    print("="*40 + "\n")

    return {
        "status": "success",
        "data": {
            "banks": banks,
            "names": names,
            "accounts": account_numbers,
            "raw_text": clean_lines,
            "preprocessing": best_variant['label'],
        }
    }

if __name__ == "__main__":
    run_ocr_scan('test_slip.png')