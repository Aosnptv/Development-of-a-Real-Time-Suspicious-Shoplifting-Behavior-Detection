import os
import requests

class TelegramService:
    def __init__(self, token=None, chat_id=None):
        # 🟢 แนะนำให้เอาคีย์ไปใส่ใน config.json หรือใส่ตรงนี้ชั่วคราวเพื่อเทสต์ก่อนได้ครับ
        self.token = token or "8695580720:AAE8oo5qpXJZrjEApC0PblsD4a1i8-iZ4Dg"
        self.chat_id = chat_id or "7626572623"
        self.api_url = f"https://api.telegram.org/bot{self.token}"

    def send_message(self, text):
        """ส่งข้อความตัวอักษร"""
        url = f"{self.api_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            return response.json()
        except Exception as e:
            print(f"[TelegramService] Error sending message: {e}")
            return None

    def send_alert_with_image(self, message, image_path):
        """ส่งข้อความแจ้งเตือนพร้อมแนบรูปภาพหลักฐาน"""
        if not os.path.exists(image_path):
            print(f"[TelegramService] Image not found: {image_path}")
            # ถ้าไม่มีรูป ให้ส่งแต่ข้อความแทน
            return self.send_message(message)

        url = f"{self.api_url}/sendPhoto"
        payload = {
            "chat_id": self.chat_id,
            "caption": message,
            "parse_mode": "Markdown"
        }
        
        try:
            with open(image_path, 'rb') as photo_file:
                files = {'photo': photo_file}
                response = requests.post(url, data=payload, files=files, timeout=15)
                return response.json()
        except Exception as e:
            print(f"[TelegramService] Error sending photo alert: {e}")
            return None