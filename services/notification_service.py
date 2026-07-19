import requests
import threading
import os


class NotificationService:
    def __init__(self):
        # 💡 ใส่ Token และ Chat ID ของคุณตรงนี้ (หรือดึงจาก ConfigManager ก็ได้)
        # วิธีเอา Token: สร้างบอตกับ @BotFather ใน Telegram
        # วิธีเอา Chat ID: ทักแชทบอต @userinfobot เพื่อดู ID ตัวเอง
        self.bot_token = "YOUR_TELEGRAM_BOT_TOKEN"
        self.chat_id = "YOUR_TELEGRAM_CHAT_ID"

    def send_alert(self, camera_id, person_id, image_path):
        """เรียกฟังก์ชันส่งข้อความและรูปภาพแบบแยก Thread เพื่อไม่ให้กล้องกระตุก"""
        if self.bot_token == "YOUR_TELEGRAM_BOT_TOKEN" or self.chat_id == "YOUR_TELEGRAM_CHAT_ID":
            print("[NotificationService] ⚠️ ยังไม่ได้ตั้งค่า Telegram Token หรือ Chat ID ข้ามการส่งแจ้งเตือน")
            return

        # แยก Thread ทำงานเบื้องหลัง (Background Thread)
        thread = threading.Thread(
            target=self._async_send, 
            args=(camera_id, person_id, image_path), 
            daemon=True
        )
        thread.start()

    def _async_send(self, camera_id, person_id, image_path):
        """ฟังก์ชันส่งข้อมูลไปที่ Telegram API"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
        
        # ข้อความที่จะส่งไปพร้อมรูปภาพ
        caption = (
            f"🚨 <b>[ALERT] พบพฤติกรรมต้องสงสัยขโมยสินค้า!</b>\n\n"
            f"📸 <b>กล้องหมายเลข:</b> {camera_id}\n"
            f"👤 <b>Person ID (AI):</b> {person_id}\n"
            f"⚠️ <b>สถานะวิเคราะห์:</b> S5 (Suspected Concealment)"
        )

        try:
            if os.path.exists(image_path):
                with open(image_path, 'rb') as photo:
                    payload = {
                        'chat_id': self.chat_id,
                        'caption': caption,
                        'parse_mode': 'HTML'
                    }
                    files = {
                        'photo': photo
                    }
                    response = requests.post(url, data=payload, files=files, timeout=10)
                    
                if response.status_code == 200:
                    print(f"🔔 [Telegram] ส่งภาพหลักฐานเข้ามือถือสำเร็จแล้ว!")
                else:
                    print(f"⚠️ [Telegram] ส่งไม่สำเร็จ Code: {response.status_code}, Response: {response.text}")
            else:
                print(f"⚠️ [Telegram] ไม่พบไฟล์ภาพหลักฐานที่ตำแหน่ง: {image_path}")
                
        except Exception as e:
            print(f"⚠️ [Telegram] เกิดข้อผิดพลาดในการเชื่อมต่อเครือข่าย: {e}")