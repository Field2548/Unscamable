#!/usr/bin/env python3
"""
Test QR blacklist checking functionality
"""
import sys
import os
import base64
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ocr-scam-guard'))

# Import the QR decoder functions directly
from ocr_scam_guard.server import QR_BLACKLIST, check_blacklist, score_payloads, decode_qr_payloads

print(f"[Test] Loaded {len(QR_BLACKLIST)} blacklist entries")
print()

# Test 1: Direct blacklist check
test_payload = "MR. Kanade Areepoonsiri\nAccount: xxx-x-x9192-x\nRef ID: 004999116153395\nPromptPay Payment"
is_blacklisted, entry = check_blacklist(test_payload)
print(f"[Test 1] Blacklist Check")
print(f"  Payload: {repr(test_payload[:50])}...")
print(f"  Is blacklisted: {is_blacklisted}")
if is_blacklisted:
    print(f"  Matched account: {entry.get('account_name')}")
print()

# Test 2: Score payloads with blacklist detection
risk_score, flags = score_payloads([test_payload])
print(f"[Test 2] Payload Scoring")
print(f"  Risk score: {risk_score}")
print(f"  Flags:")
for flag in flags:
    print(f"    - {flag}")
print()

# Test 3: Test with image file
print(f"[Test 3] QR Decoding from Image File")
test_image_path = 'test_blacklisted_qr.png'
if os.path.exists(test_image_path):
    import cv2
    img = cv2.imread(test_image_path)
    if img is not None:
        payloads = decode_qr_payloads(img)
        print(f"  Decoded {len(payloads)} QR code(s)")
        for payload in payloads:
            is_blacklisted, entry = check_blacklist(payload)
            print(f"    Payload: {payload[:50]}...")
            print(f"    Blacklisted: {is_blacklisted}")
        risk_score, flags = score_payloads(payloads)
        print(f"  Risk score: {risk_score}")
        print(f"  Flags: {flags}")
    else:
        print(f"  ERROR: Could not read image file")
else:
    print(f"  Image file not found: {test_image_path}")

print()
print("[Test] Complete!")
