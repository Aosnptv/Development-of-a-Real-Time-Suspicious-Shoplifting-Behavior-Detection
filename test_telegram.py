import os
from services.telegram_service import TelegramService

def simulate_shoplifting_detection():
    print("=== เริ่มการทดสอบระบบแจ้งเตือน Telegram ===")
    
    # 1. เรียกใช้งาน Service (อย่าลืมใส่ Token และ Chat ID ในไฟล์บริการก่อนนะ)
    tg = TelegramService()
    
    # 2. จำลองข้อความแจ้งเตือน
    alert_msg = (
        "🚨 *แจ้งเตือน: พบพฤติกรรมต้องสงสัย!* 🚨\n"
        "📷 กล้อง: Camera 01 (หน้าเคาน์เตอร์)\n"
        "🔍 ตรวจพบ: พฤติกรรม Shoplifting (หยิบของซ่อน)\n"
        "⏱️ เวลา: 15 ก.ค. 2026 - 03:00 น.\n"
        "💡 _โปรดตรวจสอบความปลอดภัย ณ จุดเกิดเหตุ_"
    )
    
    # 3. ลองทดสอบส่งเฉพาะข้อความดูก่อน
    print("1. กำลังทดสอบส่งข้อความ...")
    res_msg = tg.send_message("🔔 เปิดระบบทดสอบสัญญาณ Telegram: บอทพร้อมทำงานแล้วครับ")
    if res_msg and res_msg.get("ok"):
        print("✅ ส่งข้อความสำเร็จ!")
    else:
        print("❌ ส่งข้อความล้มเหลว ตรวจสอบ Token/Chat ID อีกครั้ง")

    # 4. จำลองการส่งภาพหลักฐาน (สร้างไฟล์ภาพหลอกๆ ขึ้นมาเทสต์)
    print("\n2. กำลังทดสอบส่งข้อความพร้อมภาพหลักฐาน...")
    test_image = "test_evidence.jpg"
    
    # เพื่อความชัวร์ในการเทสต์ เราจะเขียนโค้ดสร้างรูปภาพสีเหลี่ยมเปล่าๆ ไว้ลองส่ง
    try:
        from PIL import Image
        img = Image.new('RGB', (400, 300), color = (239, 68, 68)) # รูปสีแดงแจ้งเตือน
        img.save(test_image)
    except ImportError:
        # ถ้าไม่มีไลบรารี PIL ให้หาไฟล์ภาพอะไรก็ได้ในคอมมาเปลี่ยนชื่อเป็น test_evidence.jpg
        with open(test_image, "w") as f:
            f.write("dummy data")

    # สั่งยิงข้อมูลพร้อมรูปภาพ
    res_photo = tg.send_alert_with_image(alert_msg, test_image)
    
    if res_photo and res_photo.get("ok"):
        print("✅ ส่งภาพแจ้งเตือนเข้ามือถือสำเร็จแล้ว!")
    else:
        print("❌ ส่งภาพแจ้งเตือนล้มเหลว")
        
    # เคลียร์ไฟล์ขยะที่สร้างขึ้นมาเทสต์
    if os.path.exists(test_image):
        os.remove(test_image)

if __name__ == "__main__":
    simulate_shoplifting_detection()