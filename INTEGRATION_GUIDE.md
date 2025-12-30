# Extension ↔ OCR-Scam-Guard Integration Guide

This document describes how the **extension** and **ocr-scam-guard** services are linked together.

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
        [Optionally calls OCR service]
                ↓
        OCR-Scam-Guard (Flask)
        - Port: 5001
        - /scan endpoint
        - Analyzes images
```

## How They're Connected

### 1. **Text Analysis Flow** (Main)
- User activates extension on a webpage
- Extension extracts text via `content.js`
- `popup.js` sends text to `http://localhost:5000/analyze`
- Extension backend analyzes for scam patterns
- Results displayed in popup

### 2. **Image Analysis Flow** (Optional)
- If an image is available (future implementation)
- Extension can send base64 image data
- Extension backend forwards to OCR service at `http://localhost:5001/scan`
- OCR service analyzes image with PaddleOCR + scam detection
- Results combined and returned to extension

## Service URLs

| Service | URL | Port | Environment Variable |
|---------|-----|------|----------------------|
| Extension Backend | `http://localhost:5000` | 5000 | `FLASK_PORT` |
| OCR Backend | `http://localhost:5001` | 5001 | `OCR_PORT` |

### Configuring Service URLs

**Extension Backend** (`extension/app.py`):
```python
OCR_SERVICE_URL = os.environ.get('OCR_SERVICE_URL', 'http://localhost:5001')
```

Set custom OCR URL:
```bash
export OCR_SERVICE_URL=http://your-ocr-server:5001
```

**OCR Service** (`ocr-scam-guard/server.py`):
```python
port = int(os.environ.get('OCR_PORT', 5001))
```

Set custom port:
```bash
export OCR_PORT=5001
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
  "ocr_results": {
    "risk_score": 15,
    "flags": ["Bank logo detected"]
  }
}
```

#### `/health` (GET)
Check if extension service is running.

---

### OCR Backend

#### `/scan` (POST)
Analyze image for scams using OCR.

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
  "risk_score": 25,
  "flags": ["Transfer slip detected", "Bank account found"],
  "extracted_text": "Banking information from image",
  "bank_detected": "KBANK"
}
```

#### `/health` (GET)
Check if OCR service is running.

---

## Setup Instructions

### 1. Start OCR Service

```bash
cd ocr-scam-guard
python server.py
```

Expected output:
```
✅ LOADED: UPDATED OCR ENGINE V6 (NO ARGS)
🚀 OCR Server running on http://localhost:5001
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

### OCR Service Unreachable
- Extension backend can't reach OCR service
- **Fix:** 
  - Run OCR service: `python ocr-scam-guard/server.py`
  - Check port 5001 is available
  - Verify `OCR_SERVICE_URL` environment variable

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
- Detailed OCR results display

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
pip install -r ocr-scam-guard/requirements.txt
```

### Extension Not Communicating
1. Check browser console for errors (F12)
2. Check Flask server logs for API errors
3. Verify manifest.json includes `http://localhost:5000/*` in host_permissions

---

## Architecture Decisions

1. **Separate Services**: OCR and text analysis run on separate ports
   - Allows independent scaling
   - Can run on different machines
   - Easier debugging and maintenance

2. **Request Forwarding**: Extension backend forwards OCR requests
   - Single entry point for client
   - Easier to add authentication/logging
   - Can implement caching/rate limiting

3. **Graceful Degradation**: If OCR service is down
   - Extension still works with text analysis
   - OCR errors are caught and logged
   - User sees text-based results only

---

**Last Updated:** December 2025
