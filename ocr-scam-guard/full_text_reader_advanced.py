import os
import cv2 # Computer Vision library
import numpy as np
from paddleocr import PaddleOCR

# --- 0. FIX NETWORK CHECK ---
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'

# --- 1. SETUP PATH ---
script_dir = os.path.dirname(os.path.abspath(__file__))
img_path = os.path.join(script_dir, 'test_slip.png') 

def preprocess_image_to_negative(path):
    """
    Turns the image into a 'Negative' (Inverted Colors).
    This turns White Text (hard to read) into Black Text (easy to read).
    """
    # Read image
    img = cv2.imread(path)
    if img is None: return None
    
    # 1. Convert to Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 2. Invert (Negative)
    # White becomes Black, Blue becomes Orange/Dark
    inverted = cv2.bitwise_not(gray)
    
    # 3. Increase Contrast (Make darks darker, lights lighter)
    # alpha=1.5 (Contrast), beta=0 (Brightness)
    high_contrast = cv2.convertScaleAbs(inverted, alpha=1.5, beta=0)
    
    # 4. IMPORTANT: Convert back to "Fake Color" (3 Channels)
    # PaddleOCR crashes if you give it a 1-channel image. This fixes it.
    final_img = cv2.cvtColor(high_contrast, cv2.COLOR_GRAY2BGR)
    
    return final_img

def scan_everything():
    if not os.path.exists(img_path):
        print(f"❌ Error: Cannot find '{img_path}'")
        return

    print(f"🔍 Reading EVERYTHING in '{img_path}' (Negative Mode)...")
    
    # --- AI SETTINGS ---
    ocr = PaddleOCR(
        lang='th', 
        use_textline_orientation=True,
        text_det_thresh=0.05,         # EXTREMELY Sensitive (catch everything)
        text_det_unclip_ratio=2.5,    # Large boxes to catch edges
        text_det_limit_side_len=2500  # High Resolution
    )
    
    # --- STEP 1: PREPROCESS ---
    negative_img = preprocess_image_to_negative(img_path)
    
    if negative_img is None:
        print("❌ Error: Could not process image.")
        return

    # --- STEP 2: PREDICT ---
    results = ocr.predict(negative_img)

    all_text = []
    for res in results:
        data = res.json 
        if 'res' in data and 'rec_texts' in data['res']:
            all_text.extend(data['res']['rec_texts'])

    if not all_text:
        print("❌ No text found.")
        return

    # --- PRINT RESULTS ---
    print("\n" + "="*40)
    print("       📄 RAW FULL TEXT SCAN 📄")
    print("="*40)
    
    print("--- [Format: Full Paragraph] ---")
    print(" ".join(all_text))
    
    print("\n" + "-"*40)
    print("--- [Format: Line by Line] ---")
    for i, line in enumerate(all_text):
        print(f"{i+1}: {line}")

    print("="*40 + "\n")

if __name__ == "__main__":
    scan_everything()