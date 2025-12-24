import base64
import cv2
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from ocr_engine import run_ocr_scan

app = Flask(__name__)
CORS(app)

def base64_to_image(base64_string):
    # Fix potential header issues (data:image/jpeg;base64,...)
    if ',' in base64_string:
        base64_string = base64_string.split(',')[1]
    img_data = base64.b64decode(base64_string)
    nparr = np.frombuffer(img_data, np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)

@app.route('/scan', methods=['POST'])
def scan_image():
    try:
        data = request.json
        if 'image' not in data:
            return jsonify({"status": "error", "message": "No image provided"}), 400
        
        # 1. Decode Image
        image = base64_to_image(data['image'])
        
        # 2. Save temporarily (so ocr_engine can read it)
        temp_filename = "temp_server_scan.png"
        cv2.imwrite(temp_filename, image)
        
        # 3. Run Your Engine
        print("🔍 Analyzing image...")
        result = run_ocr_scan(temp_filename)
        
        # 4. Return JSON
        return jsonify(result)

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    print("🚀 OCR API running at http://localhost:5000/scan")
    app.run(port=5000, debug=True)