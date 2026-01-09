# Quick Start - Extension + QR Decoder

## Run Everything in 2 Steps

### Option 1: Windows
```bash
start_services.bat
```

### Option 2: macOS/Linux
```bash
bash start_services.sh
```

### Option 3: Manual (All Platforms)

**Terminal 1 - Start QR Decoder:**
```bash
cd ocr-scam-guard
python server.py
```

**Terminal 2 - Start Extension Backend:**
```bash
cd extension
python app.py
```

## Then Load the Extension

1. Open Chrome → `chrome://extensions/`
2. Enable **Developer mode** (top right)
3. Click **Load unpacked**
4. Select the `extension/` folder
5. Done! 🎉

## How It Works

```
Browser Extension
    ↓ (Text to analyze)
Extension Backend (5000)
    ↓ (Optional image)
QR Decoder (5001)
    ↓
Combined Risk Score
```

## Service Endpoints

| Service | URL | Status |
|---------|-----|--------|
| Extension | `http://localhost:5000` | `/health` |
| QR Decoder | `http://localhost:5001` | `/health` |

## Troubleshooting

**Port already in use?**
```bash
# Windows
netstat -ano | findstr :5000

# macOS/Linux
lsof -i :5000
```

**Can't import modules?**
```bash
pip install -r extension/requirements.txt
pip install -r ocr-scam-guard/requirements.txt
```

**Extension not connecting?**
- Check both Flask servers are running
- Open DevTools (F12) and check console for errors
- Verify `http://localhost:5000/*` in manifest.json

## Documentation

See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for detailed architecture and API documentation.
