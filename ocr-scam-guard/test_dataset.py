import os
from ocr_engine import run_ocr_scan

# --- CONFIGURATION ---
# This looks for the 'dataset' folder in the parent directory (Unscamable/dataset)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
DATASET_FOLDER = os.path.join(PARENT_DIR, "dataset")

def test_all_images():
    if not os.path.exists(DATASET_FOLDER):
        print(f"❌ Error: Cannot find folder at: {DATASET_FOLDER}")
        print("Please check your folder structure.")
        return

    # Get all images
    files = [f for f in os.listdir(DATASET_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    print(f"📂 Found {len(files)} images in '{DATASET_FOLDER}'\n")

    for filename in files:
        full_path = os.path.join(DATASET_FOLDER, filename)
        print(f"-------------------------------------------------")
        print(f"🖼️  Testing: {filename}")
        
        # Run your Engine
        result = run_ocr_scan(full_path)
        
        # Print a quick summary
        status = result.get('status')
        if status == 'success':
            data = result['data']
            print(f"   ✅ Bank: {data['banks']}")
            print(f"   ✅ Name: {data['names']}")
            raw_text = data.get('raw_text') or []
            if raw_text:
                print("   📜 Raw Text:")
                for line in raw_text:
                    print(f"      • {line}")
            
            # Simple Pass/Fail Logic
            if data['accounts']:
                print(f"   🚨 ACCOUNT FOUND: {data['accounts']} (SCAM TRIGGERED)")
            else:
                print("   ℹ️  No Account Found (Safe/Info Only)")
        elif status == 'empty':
            message = result.get('message', 'No readable text detected.')
            print(f"   ⚪ {message}")
        else:
            print(f"   ❌ Error: {result.get('message', 'Unknown error')}")
            
    print("\n-------------------------------------------------")
    print("✅ Dataset Test Complete.")

if __name__ == "__main__":
    test_all_images()