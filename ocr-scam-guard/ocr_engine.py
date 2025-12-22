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


# --- 3. HELPER FUNCTIONS ---

def get_ocr_engine():
    global _OCR_INSTANCE
    if _OCR_INSTANCE is None:
        _OCR_INSTANCE = PaddleOCR(
            lang='th',
            use_textline_orientation=True,
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


def generate_preprocess_variants(image):
    """Generate targeted presets to cover varied OCR edge cases."""
    variants = []
    
    # 1. Check Skew (Run on resized copy to be fast)
    small_img = smart_resize(image)
    _, angle = deskew_image(small_img)
    
    # We use original image for processing, but deskew if needed
    if abs(angle) >= 0.5:
        # Deskew the potentially large image (carefully)
        base_img, _ = deskew_image(image) 
    else:
        base_img = image

    # 2. Variant A: Balanced (General Purpose)
    balanced_img, brightness = balanced_preprocess(base_img)
    variants.append(("balanced", balanced_img))

    # Upscaled variant aimed at tiny timestamps or UI text
    upscaled_img = upscaled_preprocess(base_img)
    variants.append(("upscaled", upscaled_img))

    # CLAHE variant highlights light text within colored bubbles
    clahe_img = clahe_preprocess(base_img)
    variants.append(("clahe", clahe_img))

    # Unsharp mask variant helps with soft-focus captures
    unsharp_img = unsharp_preprocess(base_img)
    variants.append(("unsharp", unsharp_img))

    # Binary variant remains focused on numeric clarity
    binary_img = binary_preprocess(base_img)
    variants.append(("binary", binary_img))

    return variants, brightness

def merge_lines(boxes, texts, y_threshold=15): 
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

    # 1. Preprocess (Fast Mode)
    variants, brightness = generate_preprocess_variants(base_img)
    
    ocr = get_ocr_engine()
    variant_results = []

    # 2. Run OCR Loop with Progress Bar
    total_variants = len(variants)
    for i, (label, variant_img) in enumerate(variants):
        print(f"   👉 Processing variant {i+1}/{total_variants}: {label}...")
        
        ocr_output = ocr.predict(variant_img)
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

        boxes = [item['box'] for item in cleaned_items]
        texts = [item['text'] for item in cleaned_items]
        merged_lines = merge_lines(boxes, texts, y_threshold=15)

        avg_score = sum(item['score'] for item in cleaned_items) / len(cleaned_items) if cleaned_items else 0
        
        variant_results.append({
            'label': label,
            'lines': merged_lines,
            'quality': avg_score,
        })

    if not variant_results:
        return {"status": "empty", "data": {}}

    # 3. Pick Winner
    best_variant = max(variant_results, key=lambda v: v['quality'])
    
    clean_lines = best_variant['lines']
    full_text_blob = " ".join(clean_lines)
    clean_text_blob = full_text_blob.replace("-", "").replace(" ", "")

    account_numbers = re.findall(r'\d{10,12}', clean_text_blob)
    banks = extract_bank(clean_lines)
    names = [dedupe_line_tokens(name) for name in extract_name(clean_lines)]
    names = [name for name in names if name]

    return {
        "status": "success",
        "data": {
            "banks": banks,
            "names": names,
            "accounts": account_numbers,
            "raw_text": clean_lines
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