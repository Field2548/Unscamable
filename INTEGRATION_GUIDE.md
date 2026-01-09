# Extension ↔ QR Decoder Integration Guide

This document describes how the **extension** and **QR decoder** services are linked together.

## Architecture Overview

```
Browser Extension (Chrome)
    ↓
    ├─ popup.js (UI)
    ├─ content.js (text extraction)
    └─ service_worker.js (icon management)
                ↓
        Extension Backend (Flask)
        - Port: 5000
        - /analyze endpoint
        - Handles text analysis
                ↓
        [Optionally calls QR decoder]
                ↓
        QR Decoder (Flask + OpenCV)
        - Port: 5001
        - /decode endpoint
        - Decodes QR payloads and scores risk
```

## How They're Connected

### 1. **Text Analysis Flow** (Main)
- User activates extension on a webpage
- Extension extracts text via `content.js`
- `popup.js` sends text to `http://localhost:5000/analyze`
- Extension backend analyzes for scam patterns
- Results displayed in popup

### 2. **Image/QR Analysis Flow** (Optional)
- If an image is available (future implementation)
- Extension can send base64 image data
- Extension backend forwards to QR decoder at `http://localhost:5001/decode`
- QR decoder extracts QR payload(s), detects risky URLs/payment cues
- Results combined and returned to extension

## Service URLs

| Service | URL | Port | Environment Variable |
|---------|-----|------|----------------------|
| Extension Backend | `http://localhost:5000` | 5000 | `FLASK_PORT` |
| QR Decoder | `http://localhost:5001` | 5001 | `QR_DECODER_PORT` |

### Configuring Service URLs

**Extension Backend** (`extension/app.py`):
```python
QR_DECODER_URL = os.environ.get('QR_DECODER_URL', 'http://localhost:5001')
```

Set custom QR decoder URL:
```bash
export QR_DECODER_URL=http://your-qr-decoder:5001
```

**QR Decoder Service** (`ocr-scam-guard/server.py`):
```python
port = int(os.environ.get('QR_DECODER_PORT', 5001))
```

Set custom port:
```bash
export QR_DECODER_PORT=5001
```

## API Endpoints

### Extension Backend

#### `/analyze` (POST)
Analyze text and optionally combined with image analysis.

**Request:**
```json
{
  "text": "User message to analyze",
  "image": "base64_encoded_image_optional"
}
```

**Response:**
```json
{
  "risk_score": 45,
  "status": "Warning",
  "color": "#FFA726",
  "flags": ["Suspicious terms found"],
  "entities_found": ["123-4-56789-0"],
  "qr_results": {
    "risk_score": 15,
    "flags": ["QR code links to URL: https://bit.ly/..."]
  }
}
```

#### `/health` (GET)
Check if extension service is running.

---

### QR Decoder Backend

#### `/decode` (POST)
Decode QR codes from an image and score basic risk.

**Request:**
```json
{
  "image": "base64_encoded_image"
}
```

**Response:**
```json
{
  "status": "success",
  "status": "success",
  "decoded_payloads": ["https://bit.ly/pay-now"],
  "risk_score": 25,
  "flags": ["QR code links to URL: https://bit.ly/pay-now", "Shortened URL detected (bit.ly)"]
}
```

#### `/health` (GET)
Check if QR decoder service is running.

---

## Setup Instructions

### 1. Start QR Decoder Service

```bash
cd ocr-scam-guard
python server.py
```

Expected output:
```
🚀 QR Decoder running on http://localhost:5001
```

### 2. Start Extension Backend

```bash
cd extension
python app.py
```

Expected output:
```
 * Running on http://0.0.0.0:5000
```

### 3. Load Extension in Chrome

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (top right)
3. Click "Load unpacked"
4. Select the `extension/` folder
5. Extension should appear with icon

### 4. Test the Integration

1. Go to any website with chat or messaging
2. Open the extension popup
3. Select and analyze text
4. You should see risk analysis results

---

## Error Handling

### "Backend not running. Start Flask server on port 5000"
- The extension can't reach the Flask backend
- **Fix:** Run `python extension/app.py`

### QR Decoder Unreachable
- Extension backend can't reach QR decoder
- **Fix:** 
  - Run QR decoder: `python ocr-scam-guard/server.py`
  - Check port 5001 is available
  - Verify `QR_DECODER_URL` environment variable

### CORS Errors
- Both services have `CORS()` enabled
- Ensures cross-origin requests work
- If issues persist, check Flask-CORS is installed

---

## Future Enhancements

### Image Capture Integration
- Add image capture button to extension popup
- Send screenshot/cropped image to analyze endpoint
- Combine text + image analysis for comprehensive scam detection

### Real-time Image Analysis
- Analyze transfer slips, bank statements
- Detect forged documents
- Extract bank account information automatically

### Batch Processing
- Queue multiple images for analysis
- Progress tracking
- Detailed QR decoding results display

---

## Troubleshooting

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :5000
kill -9 <PID>
```

### Module Import Errors
Ensure all dependencies are installed:
```bash
pip install -r extension/requirements.txt
pip install flask flask-cors opencv-python numpy
```

### Extension Not Communicating
1. Check browser console for errors (F12)
2. Check Flask server logs for API errors
3. Verify manifest.json includes `http://localhost:5000/*` in host_permissions

---

## Architecture Decisions

1. **Separate Services**: QR decoding and text analysis run on separate ports
   - Allows independent scaling
   - Can run on different machines
   - Easier debugging and maintenance

2. **Request Forwarding**: Extension backend forwards QR decoding requests
   - Single entry point for client
   - Easier to add authentication/logging
   - Can implement caching/rate limiting

3. **Graceful Degradation**: If QR decoder is down
   - Extension still works with text analysis
  - QR decoding errors are caught and logged
   - User sees text-based results only

---

**Last Updated:** December 2025
