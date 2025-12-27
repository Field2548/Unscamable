import re

# Risk Score regex patterns
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
#

# Chat Extraction regex patterns
TIMESTAMP_REGEX = re.compile(r"\b\d{1,2}:\d{2}\s?(AM|PM)?\b", re.IGNORECASE)
DATE_REGEX = re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b")
#

# Chat Normalization regex patterns 
EMOJI_REGEX = re.compile(
    "[" 
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "]+",
    flags=re.UNICODE
)
REPEATED_PUNCT = re.compile(r"([!?.]){2,}")
POLITE_PARTICLES = re.compile(r"(ครับ|ค่ะ|นะครับ|นะคะ)")
#