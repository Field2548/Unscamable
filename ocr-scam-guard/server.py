import base64
import cv2
import numpy as np
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS
from ocr_engine import run_ocr_scan

app = Flask(__name__)
CORS(app)

def base64_to_image(base64_string):
    """
    Decodes a base64 string into an OpenCV image.
    Handles 'data:image/jpeg;base64,' headers if present.
    """
    if ',' in base64_string:
        base64_string = base64_string.split(',')[1]
    
    img_data = base64.b64decode(base64_string)
    nparr = np.frombuffer(img_data, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return image

@app.route('/scan', methods=['POST'])
def scan_image():
    try:
        data = request.json
        # Check if data exists
        if not data or 'image' not in data:
            return jsonify({"status": "error", "message": "No image provided"}), 400
        
        # 1. Decode Image
        image = base64_to_image(data['image'])
        if image is None:
             return jsonify({"status": "error", "message": "Failed to decode image"}), 400

        # 2. Save temporarily
        temp_filename = "temp_server_scan.png"
        cv2.imwrite(temp_filename, image)
        
        # 3. Run Your Engine
        print(f"🔍 Analyzing image size: {image.shape}...")
        result = run_ocr_scan(temp_filename)
        
        return jsonify(result)

    except Exception as e:
        print("❌ CRITICAL SERVER ERROR:")
        traceback.print_exc() # This prints the exact line number of the error
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    print("🚀 OCR Server running on http://localhost:5000")
    app.run(port=5000, debug=True)