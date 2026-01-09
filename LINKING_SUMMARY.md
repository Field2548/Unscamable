# Extension ↔ QR Decoder Linking Summary

## What Was Implemented

I've successfully linked the **extension** and **QR decoder** services together. Here's what changed:

---

## 🔗 Code Changes

### 1. **Extension Backend** (`extension/app.py`)
**Added/Updated:**
- ✅ `QR_DECODER_URL` configuration (defaults to `http://localhost:5001`)
- ✅ `decode_image_with_qr_service()` to forward image data to the QR decoder
- ✅ Enhanced `/analyze` endpoint to:
  - Accept optional `image` parameter
  - Forward image to QR decoder if provided
  - Combine text + QR risk scores
  - Merge QR flags with text analysis flags

**Benefits:**
- Extension can now analyze both text AND QR payloads
- Graceful fallback if QR decoder is down
- Configurable QR decoder URL via environment variables

### 2. **QR Decoder Service** (`ocr-scam-guard/server.py`)
**Added/Updated:**
- ✅ `/decode` endpoint to extract QR payloads and score risk
- ✅ `/health` endpoint for service availability checks
- ✅ Configurable port via `QR_DECODER_PORT` environment variable (defaults to 5001)
- ✅ CORS enabled for cross-service communication

**Benefits:**
- Clear separation of services (extension on 5000, QR decoder on 5001)
- Extension can verify QR decoder is running before sending requests
- Production-ready configuration

---

## 📁 New Files Created

### Configuration Files
- **`.env.example` (extension)** - Environment variables template
- **`.env.example` (ocr-scam-guard)** - Environment variables template

### Documentation
- **`INTEGRATION_GUIDE.md`** - Complete integration architecture and API documentation
- **`QUICK_START.md`** - Quick reference for getting started

### Startup Scripts
- **`start_services.bat`** - Windows batch script to start both services
- **`start_services.sh`** - Bash script for macOS/Linux

### Deployment
- **`docker-compose.yml`** - Docker Compose configuration for containerized deployment

---

## 🔄 How They Connect Now

```
┌─────────────────────────────────────────────────────────┐
│         Chrome Browser Extension                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ popup.js → content.js (extract text & images)   │   │
│  └──────────────────┬──────────────────────────────┘   │
└─────────────────────┼──────────────────────────────────┘
                      │ POST /analyze
                      │ {text, image}
                      ↓
         ┌────────────────────────────┐
         │ Extension Backend (5000)   │
         │ • Analyzes text            │
         │ • Calls QR decoder if image given │
         │ • Combines scores          │
         └────────────┬───────────────┘
                      │ POST /scan
                      │ {image}
                      ↓
         ┌────────────────────────────┐
         │ QR Decoder (5001)          │
         │ • QR payload decoding      │
         │ • Risk scoring             │
         │ • Risk scoring             │
         └────────────┬───────────────┘
                      │ Response
                      ↓
         ┌────────────────────────────┐
         │ Combined Risk Assessment   │
         │ • Text flags               │
         │ • QR flags                 │
         │ • Risk score 0-100         │
         │ • Status & Color           │
         └────────────────────────────┘
```

---

## 🚀 Quick Start

### All-in-One (Windows):
```bash
start_services.bat
```

### All-in-One (macOS/Linux):
```bash
bash start_services.sh
```

### Manual Start (All Platforms):

**Terminal 1:**
```bash
cd ocr-scam-guard
python server.py
```

**Terminal 2:**
```bash
cd extension
python app.py
```

Then load extension in Chrome:
1. Go to `chrome://extensions/`
2. Enable Developer mode
3. Click "Load unpacked" 
4. Select `extension/` folder

---

## 📡 API Endpoints

### Extension Backend (http://localhost:5000)

**POST `/analyze`**
```json
Request: { "text": "...", "image": "base64..." }
Response: { 
  "risk_score": 50,
  "status": "Warning",
  "flags": [...],
  "qr_results": { ... }
}
```

**GET `/health`** - Check if service is running

---

### QR Decoder (http://localhost:5001)

**POST `/decode`**
```json
Request: { "image": "base64..." }
Response: { 
  "decoded_payloads": ["https://..."],
  "risk_score": 25,
  "flags": [...]
}
```

**GET `/health`** - Check if service is running

---

## ⚙️ Configuration

### Environment Variables

**Extension Backend:**
```bash
QR_DECODER_URL=http://localhost:5001  # Where QR decoder is running
FLASK_PORT=5000
FLASK_ENV=production
```

**QR Decoder:**
```bash
QR_DECODER_PORT=5001
FLASK_ENV=production
```

---

## 🛡️ Error Handling

Both services gracefully handle failures:

1. **QR Decoder Down:**
  - Extension still analyzes text
  - Returns text-only results
  - QR results are `None`

2. **Network Issues:**
   - Timeout after 10 seconds
   - Logged to console
   - Extension continues normally

3. **Invalid Data:**
   - Returns 400 error with message
   - Extension displays error to user

---

## 📦 Dependencies

### Extension Backend
- Flask==3.0.0
- flask-cors==4.0.0
 - requests (for QR decoder communication)

### QR Decoder
- flask
- flask-cors
- opencv-python
- numpy
- opencv-python
- numpy

---

## 🎯 What's Next?

To fully utilize the image analysis:

1. **Extend `content.js`** to capture images from webpages
2. **Update `popup.js`** to display image analysis toggle
3. **Add image upload** in popup UI
4. **Handle screenshot captures** of transfer slips

These enhancements would enable:
- Automatic bank slip detection
- Forged document identification
- Account number extraction
- Transfer confirmation verification

---

## 📚 Full Documentation

See **[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)** for:
- Detailed architecture
- Complete API documentation
- Setup instructions
- Troubleshooting guide
- Future enhancement ideas

---

**Status:** ✅ Complete integration ready for testing

Last updated: December 30, 2025
