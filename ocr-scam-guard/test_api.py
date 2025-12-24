import requests
import base64
import os
import json

# CONFIGURATION
# Make sure this image name matches a real file in your folder!
IMAGE_PATH = "test_slip.png" 
API_URL = "http://localhost:5000/scan"

def test_api():
    # 1. Check if image exists
    if not os.path.exists(IMAGE_PATH):
        print(f"❌ Error: Could not find image at: {IMAGE_PATH}")
        print("Please make sure you have a 'test_slip.png' in this folder.")
        return

    print(f"📡 Encoding {IMAGE_PATH} to Base64...")
    
    # 2. Convert Image to Base64 (Simulating the Browser)
    with open(IMAGE_PATH, "rb") as image_file:
        base64_string = base64.b64encode(image_file.read()).decode('utf-8')
    
    # 3. Send to Server
    payload = {"image": base64_string}
    
    try:
        print(f"🚀 Sending request to {API_URL}...")
        response = requests.post(API_URL, json=payload)
        
        # 4. Show Result
        print("\n" + "="*40)
        print("       📝 API RESPONSE")
        print("="*40)
        if response.status_code == 200:
            print(json.dumps(response.json(), indent=4, ensure_ascii=False))
        else:
            print(f"❌ Server Error {response.status_code}: {response.text}")

    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        print("👉 Make sure 'server.py' is running in another terminal!")

if __name__ == "__main__":
    test_api()