Here is a professional, clear Setup Guide formatted as a Markdown file.

You should create a new file named README.md (or SETUP_GUIDE.md) inside your ocr-scam-guard folder and paste this text inside.

This covers everything your teammate (Person C) or the Judges need to know to get your backend running without errors.

🕵️‍♂️ Scam Guard - OCR Backend Setup Guide

This is the Python Backend for the Scam Guard Extension. It uses PaddleOCR to detect text, bank names, and account numbers from images.

⚠️ CRITICAL WARNING:
This AI Engine ONLY works with Python 3.10.
Do not use Python 3.13 or 3.14, or the AI libraries will crash.

🛠️ 1. Prerequisites

Before starting, ensure you have the following installed:

Python 3.10.x (Required)

Download here: Python 3.10.11

Note: You can have multiple Python versions installed. We will force the use of 3.10 in the next steps.

Git (To pull the code)

⚙️ 2. Installation Instructions

Open your terminal (VS Code or PowerShell) and follow these steps exactly.

Step 1: Navigate to the folder
code
Powershell
download
content_copy
expand_less
cd Unscamable/ocr-scam-guard
Step 2: Create the Virtual Environment (Force Python 3.10)

We must create an isolated environment to hold the AI libraries.

code
Powershell
download
content_copy
expand_less
py -3.10 -m venv .venv

(If py doesn't work, try python3.10 -m venv .venv)

Step 3: Activate the Environment

You must see (.venv) at the start of your terminal line after this.

code
Powershell
download
content_copy
expand_less
.venv\Scripts\activate
Step 4: Install Dependencies

Copy and paste this command to install all required libraries (PaddleOCR, Flask, OpenCV):

code
Powershell
download
content_copy
expand_less
pip install paddlepaddle paddleocr flask flask-cors opencv-python "numpy<2.0"

> Note: We force numpy<2.0 because newer versions break PaddleOCR.

🚀 3. How to Run the Server

Whenever you want to use the OCR Engine, follow these two steps:

Activate the Environment:

code
Powershell
download
content_copy
expand_less
.venv\Scripts\activate

Start the Server:

code
Powershell
download
content_copy
expand_less
python server.py

Success Message:
You should see:

code
Text
download
content_copy
expand_less
🚀 OCR Server running on http://localhost:5000

Note: The first run might take 1-2 minutes to download the AI models.

📡 4. API Usage (For Frontend/Extension)

Endpoint: POST http://localhost:5000/scan

Request Body (JSON):

code
JSON
download
content_copy
expand_less
{
  "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
}

Response (JSON):

code
JSON
download
content_copy
expand_less
{
  "status": "success",
  "data": {
    "banks": ["KBNK", "SCB"],
    "accounts": ["1234567890"],
    "names": ["MR JOHN DOE"],
    "is_slip": true,
    "warning_flags": ["HIGH_RISK_WALLET_DETECTED"]
  }
}
❌ Troubleshooting

Error: ModuleNotFoundError: No module named 'paddle'

Fix: You are likely running Python 3.13. Delete the .venv folder and repeat Installation Step 2 using py -3.10.

Error: could not convert string to float

Fix: Ensure you installed numpy<2.0. Run: pip install "numpy<2.0" --force-reinstall.

Error: OneDrive Sync / Permission Denied

Fix: Pause OneDrive syncing while installing libraries, or move the project folder to C:\Dev.