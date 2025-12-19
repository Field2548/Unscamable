import re

REGEX = {
    "url": re.compile(r"(http[s]?://|www\.|bit\.ly|tinyurl|\.xyz|\.top)"),
    "money": re.compile(r"\d+(,\d+)?\s*บาท"),
    "time_pressure": re.compile(r"\d+\s*(ชั่วโมง|วัน)"),
    "otp": re.compile(r"(OTP|รหัส OTP)")
}

REGEX_WEIGHT = {
    "url": 20,
    "money": 10,
    "time_pressure": 10,
    "otp": 25
}

