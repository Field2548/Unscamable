# QR Decoder Backend Setup Guide

This service decodes QR codes from images and returns any payloads plus a simple risk score (e.g., shortened URLs or payment wording). It backs the browser extension at `http://localhost:5001` on the `/decode` endpoint.

## 1) Prerequisites
- Python 3.10+ (3.11 works fine)
- Git (to pull the repo)

## 2) Install
```bash
cd Unscamable/ocr-scam-guard
python -m venv .venv
.venv\Scripts\activate          # PowerShell/cmd
# or: source .venv/bin/activate   # macOS/Linux
pip install flask flask-cors opencv-python numpy
```

## 3) Run
```bash
.venv\Scripts\activate          # ensure the venv is active
python server.py
```

You should see:
```
🚀 QR Decoder running on http://localhost:5001
```

## 4) API
- POST `http://localhost:5001/decode`
```json
{
  "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
}
```

Sample response:
```json
{
  "status": "success",
  "decoded_payloads": ["https://bit.ly/pay-now"],
  "risk_score": 25,
  "flags": ["QR code links to URL: https://bit.ly/pay-now", "Shortened URL detected (bit.ly)"]
}
```

## 5) Troubleshooting
- `ModuleNotFoundError`: activate the venv and reinstall deps.
- `ImportError: cv2`: ensure `opencv-python` installed inside the venv.
- Port in use: free port 5001 or set `QR_DECODER_PORT` and restart.