import os
import re
from paddleocr import PaddleOCR

# --- CONFIGURATION ---
img_path = 'test_slip0.png' 

# --- KNOWLEDGE BASE ---
THAI_BANKS = {
    "kbank": ["kasikorn", "kbank", "กสิกร", "ก.ส.ก."],
    "scb": ["scb", "commercial", "ไทยพาณิชย์"],
    "ktb": ["krungthai", "ktb", "กรุงไทย"],
    "bbl": ["bangkok bank", "bbl", "กรุงเทพ"],
    "gsb": ["gsb", "government savings", "ออมสิน"],
    "ttb": ["ttb", "tmb", "thanachart", "ทหารไทย", "ธนชาต"],
    "bay": ["krungsri", "bay", "กรุงศรี"],
}

NAME_PREFIXES = ["นาย", "นาง", "น.ส.", "ด.ช.", "ด.ญ.", "mr", "mrs", "miss", "ms"]

def merge_lines(boxes, texts, y_threshold=20): 
    if not boxes or not texts: return []
    lines = []
    for box, text in zip(boxes, texts):
        try:
            # Try Polygon center
            y_center = (box[0][1] + box[2][1]) / 2
            x_start = box[0][0]
        except (TypeError, IndexError):
            # Fallback Rect center
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
    for line in text_list:
        clean_line = line.strip().lower()
        for prefix in NAME_PREFIXES:
            if clean_line.startswith(prefix):
                possible_names.append(line)
                break
    return possible_names

def run_ocr_scan():
    if not os.path.exists(img_path):
        print(f"❌ Error: Cannot find '{img_path}'")
        return

    print(f"🔍 Scanning '{img_path}' (Stable Mode)...")
    
    # --- BEST SETTINGS FOR SLIPS ---
    # We removed Inversion (because it broke the image).
    # We kept High Res (2500) to ensure the Thai Name is readable.
    ocr = PaddleOCR(
        lang='th', 
        use_textline_orientation=True,
        text_det_thresh=0.1,          # High sensitivity (Catches "Johnny")
        text_det_unclip_ratio=2.0,    # Good for Thai tone marks
        text_det_limit_side_len=2500  # High Resolution
    )
    
    results = ocr.predict(img_path)

    raw_boxes = []
    raw_texts = []
    
    for res in results:
        data = res.json 
        if 'res' in data:
            if 'rec_polys' in data['res']: raw_boxes.extend(data['res']['rec_polys'])
            elif 'rec_boxes' in data['res']: raw_boxes.extend(data['res']['rec_boxes'])
            if 'rec_texts' in data['res']: raw_texts.extend(data['res']['rec_texts'])

    if not raw_texts:
        print("❌ No text found.")
        return

    clean_lines = merge_lines(raw_boxes, raw_texts, y_threshold=20)

    # Logic Processing
    full_text_blob = " ".join(clean_lines)
    clean_text_blob = full_text_blob.replace("-", "").replace(" ", "")

    account_numbers = re.findall(r'\d{10,12}', clean_text_blob)
    banks = extract_bank(clean_lines)
    names = extract_name(clean_lines)

    # --- FINAL REPORT ---
    print("\n" + "="*40)
    print("       🕵️ SCAM GUARD REPORT 🕵️")
    print("="*40)
    
    print(f"🏦 Bank Detected:    {banks if banks else 'Unknown'}")
    print(f"👤 Name Detected:    {names if names else 'Not found'}")
    print(f"🔢 Account No:       {account_numbers if account_numbers else 'None (or Masked)'}")
    
    print("-" * 40)
    print("📜 FULL RAW MESSAGE (Line by Line):")
    
    for line in clean_lines:
        print(f"📄 Text: {line}")
        
    print("="*40 + "\n")

if __name__ == "__main__":
    run_ocr_scan()
