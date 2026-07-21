import cv2
import time
from ultralytics import YOLO

# 1. โหลดโมเดล YOLO
model_path = "models/services/shoplifting_yolov8.pt"
model = YOLO(model_path)

# 🔍 1. สั่งพิมพ์เพื่อดู Index ที่แท้จริงของโมเดลบน Terminal/PowerShell
print("--------------------------------------------------")
print("📌 Class ID เดิมที่ฝังอยู่ในไฟล์ .pt คือ:")
print(model.names)
print("--------------------------------------------------")

# 🟢 2. กำหนด Dictionary สลับชื่อ Class ให้ถูกต้อง
# (ให้ดูผลลัพธ์จาก print ด้านบน แล้วปรับเลข Index 0, 1, 2, 3... ให้ตรงกับชื่อที่ถูกต้อง)
custom_names = {
    0: 'person',
    1: 'basket',  # 👈 กำหนด Index ของ basket ให้ถูกต้อง
    2: 'hand',    # 👈 กำหนด Index ของ hand ให้ถูกต้อง
    3: 'product'  # 👈 (ใส่ Class อื่นๆ ที่มีให้ครบตามโมเดลของคุณ)
}

# อัปเดตชื่อ Class เข้าไปในโมเดล
model.names = custom_names
if hasattr(model, 'model') and hasattr(model.model, 'names'):
    model.model.names = custom_names

# 2. ใส่ชื่อไฟล์วิดีโอที่ต้องการทดสอบ
video_path = "C:/Users/deeny/Videos/AI/pick_ (10).mp4" 
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print("❌ ไม่สามารถเปิดไฟล์วิดีโอได้ กรุณาตรวจสอบ Path ไฟล์")
    exit()

# 🟢 กำหนดค่าเป้าหมาย: ความเร็วที่ต้องการให้เล่น (60 FPS)
TARGET_FPS = 60
TIME_PER_FRAME = 1.0 / TARGET_FPS

print(f"🚀 เริ่มต้นการทดสอบ... ล็อกความเร็วที่ประมาณ {TARGET_FPS} FPS")
print("กรุณากด 'q' เพื่อเลิกทำงาน")

# กำหนดชื่อหน้าต่างและทำให้สามารถปรับขนาดได้ (Resizable Window)
window_name = "shoplifting"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL) 
cv2.resizeWindow(window_name, 1280, 720) 

while cap.isOpened():
    start_time = time.time() 

    ret, frame = cap.read()
    if not ret:
        # วนลูปเล่นวิดีโอใหม่เมื่อจบไฟล์
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        continue

    # 3. ให้ YOLO ตรวจจับวัตถุในเฟรม
    results = model(frame) 

    # 4. วาด Bounding Box ผลลัพธ์การตรวจจับลงบนภาพ
    annotated_frame = results[0].plot()

    # 5. แสดงผลบนหน้าจอ
    cv2.imshow(window_name, annotated_frame)

    # 🟢 ควบคุม FPS ให้แม่นยำ
    process_time = time.time() - start_time
    delay_time = max(0.001, TIME_PER_FRAME - process_time)
    time.sleep(delay_time)

    # กด 'q' เพื่อออกจากโปรแกรม
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("👋 เลิกทำงานเรียบร้อยแล้ว")