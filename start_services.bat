@echo off
REM Startup script for Extension + QR-decoder integration
REM This script starts both services in separate terminals on Windows

echo ======================================
echo Unscamable - Extension Integration
echo ======================================
echo.

REM Check if we're in the right directory
if not exist "extension" (
    echo Error: extension folder not found
    echo Please run this script from the root directory
    exit /b 1
)

if not exist "ocr-scam-guard" (
    echo Error: ocr-scam-guard folder not found
    echo Please run this script from the root directory
    exit /b 1
)

echo Starting services...
echo.

REM Start QR Decoder service in new window
echo [1/2] Starting QR Decoder on port 5001...
start "QR-Decoder" cmd /k "cd ocr-scam-guard && python server.py"

REM Wait a moment for QR decoder to start
timeout /t 2 /nobreak

REM Start Extension Backend in new window
echo [2/2] Starting Extension Backend on port 5000...
start "Extension Backend" cmd /k "cd extension && python app.py"

echo.
echo ======================================
echo Services are starting...
echo ======================================
echo.
echo Extension Backend: http://localhost:5000
echo QR Decoder:       http://localhost:5001
echo.
echo Open Chrome and:
echo 1. Go to chrome://extensions/
echo 2. Enable "Developer mode"
echo 3. Click "Load unpacked"
echo 4. Select the extension/ folder
echo.
echo Close either terminal window to stop that service
echo.
