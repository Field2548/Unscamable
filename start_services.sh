#!/bin/bash
# Startup script for Extension + OCR-Scam-Guard integration
# This script starts both services in separate terminals on macOS/Linux

echo "======================================"
echo "Unscamable - Extension Integration"
echo "======================================"
echo ""

# Check if we're in the right directory
if [ ! -d "extension" ]; then
    echo "Error: extension folder not found"
    echo "Please run this script from the root directory"
    exit 1
fi

if [ ! -d "ocr-scam-guard" ]; then
    echo "Error: ocr-scam-guard folder not found"
    echo "Please run this script from the root directory"
    exit 1
fi

echo "Starting services..."
echo ""

# Start OCR Service in background
echo "[1/2] Starting OCR-Scam-Guard on port 5001..."
cd ocr-scam-guard
python server.py &
OCR_PID=$!

# Wait a moment for OCR service to start
sleep 2

# Start Extension Backend in background
echo "[2/2] Starting Extension Backend on port 5000..."
cd ../extension
python app.py &
EXT_PID=$!

echo ""
echo "======================================"
echo "Services are running..."
echo "======================================"
echo ""
echo "Extension Backend: http://localhost:5000"
echo "OCR Service:      http://localhost:5001"
echo ""
echo "Open Chrome and:"
echo "1. Go to chrome://extensions/"
echo "2. Enable 'Developer mode'"
echo "3. Click 'Load unpacked'"
echo "4. Select the extension/ folder"
echo ""
echo "Services PIDs: Extension=$EXT_PID, OCR=$OCR_PID"
echo ""
echo "To stop services, run: kill $OCR_PID $EXT_PID"
echo ""

# Wait for both processes
wait
