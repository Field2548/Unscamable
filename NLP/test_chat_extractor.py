from chat_extractor import extract_chat_messages

raw_chat = """
12:01 PM
ขนส่งไม่สามารถจัดส่งพัสดุได้

12:02 PM
กรุณายืนยันที่อยู่

You
โอเคครับ
"""

raw_chat1 = """09:01 AM
ด่วน!!! 10:02 AM
พัสดุของคุณไม่สามารถจัดส่งได้นะครับ You
โอเคครับ """

raw_chat2 = ["""13:01 PM
กรุณายืนยันตัวตน, 15:02 PM
ภายใน 24 ชั่วโมง, You
โอเคครับ """ ]

raw_chat3 = """
08:45 AM
พัสดุของคุณถูกระงับชั่วคราว

08:46 AM
กรุณาคลิกลิงก์เพื่อยืนยันข้อมูลการจัดส่ง

You
รับทราบครับ
"""

raw_chat4 = """
19:12 PM
ไม่สามารถจัดส่งพัสดุได้เนื่องจากข้อมูลไม่ครบถ้วน

19:13 PM
กรุณายืนยันภายในวันนี้

You
โอเคครับ
"""

raw_chat5 = """10:15 AM
แจ้งเตือนด่วน! พัสดุของคุณถูกตีกลับ กรุณายืนยันที่อยู่ You
รับทราบครับ"""

raw_chat6 = ["""07:30 AM
บัญชีขนส่งของคุณมีปัญหา, 07:31 AM
กรุณายืนยันตัวตนภายใน 12 ชั่วโมง, You
รับทราบครับ"""]

print("raw_chat0")
print(extract_chat_messages(raw_chat))
print("-----")
print("raw_chat1")
print(extract_chat_messages(raw_chat1))
print("-----")
print("raw_chat2")
print(extract_chat_messages(raw_chat2))
print("-----")
print("raw_chat3")
print(extract_chat_messages(raw_chat3))
print("-----")
print("raw_chat4")
print(extract_chat_messages(raw_chat4))
print("-----")
print("raw_chat5")
print(extract_chat_messages(raw_chat5))
print("-----")
print("raw_chat6")
print(extract_chat_messages(raw_chat6))