import cv2
import time  # 🟢 เพิ่ม: โมดูลสำหรับจับเวลาและหน่วงเวลา
from ultralytics import YOLO

# 1. โหลดโมเดล YOLO ของคุณ
model_path = "models/services/shoplifting_yolov8.pt"
model = YOLO(model_path) 

# 2. ใส่ชื่อไฟล์วิดีโอที่ต้องการทดสอบ
video_path = "C:/Users/deeny/Videos/AI/pick_ (10).mp4" 
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print("❌ ไม่สามารถเปิดไฟล์วิดีโอได้ กรุณาตรวจสอบ Path ไฟล์")
    exit()

# 🟢 กำหนดค่าเป้าหมาย: ความเร็วที่ต้องการให้เล่น (30 FPS)
TARGET_FPS = 60
# 🟢 คำนวณเวลาที่แต่ละเฟรมควรจะแสดงผล (ในหน่วยวินาที)
TIME_PER_FRAME = 1.0 / TARGET_FPS

print(f"🚀 เริ่มต้นการทดสอบ... ล็อกความเร็วที่ประมาณ {TARGET_FPS} FPS")
print("กรุณากด 'q' เพื่อเลิกทำงาน")

# กำหนดชื่อหน้าต่างและทำให้สามารถปรับขนาดได้ (Resizable Window)
window_name = "shoplifting"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL) 

# กำหนดขนาดหน้าต่างเริ่มต้น (Width, Height)
cv2.resizeWindow(window_name, 1280, 720) 

while cap.isOpened():
    # 🟢 เริ่มต้นจับเวลาของเฟรมนี้
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

    # 🟢 เพิ่มลอจิกควบคุม FPS ให้แม่นยำ
    # 1. คำนวณเวลาที่ใช้ไปทั้งหมดในการอ่านเฟรม, AI ตรวจจับ, และวาดภาพ
    process_time = time.time() - start_time
    
    # 2. คำนวณเวลาที่ต้องหน่วงเพิ่มเพื่อให้ถึงเวลาของเฟรมถัดไป
    # (เอาเวลาที่ควรจะเป็น ลบออกด้วยเวลาที่ใช้ไป)
    delay_time = max(0.001, TIME_PER_FRAME - process_time)
    
    # 3. ทำการหน่วงเวลา (Sleep) จนกว่าจะถึงกำหนดเฟรมถัดไป
    time.sleep(delay_time)

    # กด 'q' เพื่อออกจากโปรแกรม
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("👋 เลิกทำงานเรียบร้อยแล้ว")