from chat_grouper import group_chat_messages

message =[
  "พัสดุของคุณไม่สามารถจัดส่งได้",
  "กรุณายืนยันที่อยู่",
  "ภายใน 24 ชั่วโมง",
  "ขอบคุณครับ",
   "🚨 ด่วน!!!",
    "พัสดุของคุณไม่สามารถจัดส่งได้ครับ 🙏",
    "กรุณายืนยันที่อยู่ทันทีค่ะ",
]

grouped_messages = group_chat_messages(message)
print(grouped_messages)