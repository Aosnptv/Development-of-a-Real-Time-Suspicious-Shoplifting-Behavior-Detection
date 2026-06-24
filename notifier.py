import requests

TOKEN = "ใส่_TOKEN_ที่ได้จาก_BotFather_ที่นี่"
CHAT_ID = "ใส่_CHAT_ID_ของคุณที่นี่"

def send_telegram_alert(message, image_path=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    
    # ส่งข้อความ
    requests.post(url, data=payload)
    
    # ถ้ามีภาพหลักฐาน ให้ส่งภาพด้วย
    if image_path:
        photo_url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        with open(image_path, "rb") as photo:
            requests.post(photo_url, data={"chat_id": CHAT_ID}, files={"photo": photo})
        print("ส่งแจ้งเตือนพร้อมภาพเรียบร้อย!")