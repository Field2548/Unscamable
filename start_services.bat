@echo off
REM Startup script for Extension + OCR-Scam-Guard integration
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

REM Start OCR Service in new window
echo [1/2] Starting OCR-Scam-Guard on port 5001...
start "OCR-Scam-Guard" cmd /k "cd ocr-scam-guard && python server.py"

REM Wait a moment for OCR service to start
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
echo OCR Service:      http://localhost:5001
echo.
echo Open Chrome and:
echo 1. Go to chrome://extensions/
echo 2. Enable "Developer mode"
echo 3. Click "Load unpacked"
echo 4. Select the extension/ folder
echo.
echo Close either terminal window to stop that service
echo.
