import os
from paddleocr import PaddleOCR

# 1. Setup the image path
img_path = 'test_slip.jpg'

if not os.path.exists(img_path):
    print(f"❌ Error: Cannot find file '{img_path}'. Please make sure the image is in this folder.")
else:
    # 2. Initialize OCR (v3.0 Style)
    # use_textline_orientation=True replaces the old 'use_angle_cls=True'
    ocr = PaddleOCR(lang='th', use_textline_orientation=True)

    print(f"Processing {img_path}...")

    # 3. Run Inference (Using .predict instead of .ocr)
    # We do NOT pass cls=True here anymore.
    results = ocr.predict(img_path)

    # 4. Extract Results (v3.0 Style)
    # The 'results' is a list of Result objects. 
    print("\n--- Detection Results ---")
    
    for res in results:
        # res.json is a property that holds the data dictionary
        # The structure is: {'res': {'rec_texts': ['text1', 'text2'], ...}}
        data = res.json 
        
        if 'res' in data and 'rec_texts' in data['res']:
            text_list = data['res']['rec_texts']
            score_list = data['res']['rec_scores']
            
            # Print found text
            for i, text in enumerate(text_list):
                confidence = score_list[i]
                print(f"Text: {text} (Confidence: {confidence:.2f})")
                
            # --- Role B Logic: Search for Accounts ---
            # Now you have a clean list of strings (text_list) to feed into your Regex!
            import re
            full_text = "".join(text_list)
            # Basic Thai Bank Account Regex (10-12 digits)
            accounts = re.findall(r'\b\d{10,12}\b', full_text.replace("-", "").replace(" ", ""))
            if accounts:
                print(f"\n[!] Possible Account Numbers Found: {accounts}")
        else:
            # Fallback if structure is different
            res.print()
