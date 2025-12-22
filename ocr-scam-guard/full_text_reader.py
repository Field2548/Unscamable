import os
import cv2
from paddleocr import PaddleOCR

# --- 0. FIX NETWORK CHECK ---
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'

# --- 1. SETUP PATH ---
script_dir = os.path.dirname(os.path.abspath(__file__))
img_path = os.path.join(script_dir, 'test_slip.png') 

def scan_everything():
    if not os.path.exists(img_path):
        print(f"❌ Error: Cannot find '{img_path}'")
        return

    print(f"🔍 Reading EVERYTHING in '{img_path}'...")
    
    # --- AI SETTINGS (High Res Mode) ---
    # We keep these settings so it can read the small chat bubbles
    ocr = PaddleOCR(
        lang='th', 
        use_textline_orientation=True,
        text_det_thresh=0.1,          
        text_det_unclip_ratio=2.0,    
        text_det_limit_side_len=2500 
    )
    
    # Scan the image
    results = ocr.predict(img_path)

    # --- EXTRACT EVERYTHING ---
    all_text = []
    
    for res in results:
        data = res.json 
        if 'res' in data and 'rec_texts' in data['res']:
            # This gets EVERY text block found in the image
            all_text.extend(data['res']['rec_texts'])

    if not all_text:
        print("❌ The image appears to be empty (no text found).")
        return

    # --- PRINT RESULTS ---
    print("\n" + "="*40)
    print("       📄 RAW FULL TEXT SCAN 📄")
    print("="*40)
    
    # Method 1: Print Line by Line (How the AI sees it)
    print("--- [Format: Line by Line] ---")
    for i, line in enumerate(all_text):
        print(f"{i+1}: {line}")

    print("\n" + "-"*40 + "\n")

    # Method 2: Print as One Big Paragraph (Like a human reading)
    print("--- [Format: Full Paragraph] ---")
    full_paragraph = " ".join(all_text)
    print(full_paragraph)
    
    print("="*40 + "\n")

if __name__ == "__main__":
    scan_everything()