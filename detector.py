import cv2
from ultralytics import YOLO

# โหลดโมเดล YOLOv8 (ใช้รุ่นเล็กสุด 'n' เพื่อความรวดเร็ว)
model = YOLO('yolov8n.pt') 

# เปิดกล้อง Webcam (0 คือกล้องตัวแรก) หรือใส่ Path ของไฟล์วิดีโอ
cap = cv2.VideoCapture(0)

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    # นำเฟรมภาพไปประมวลผลผ่านโมเดล
    results = model(frame)

    # วาดกรอบ (Bounding Box) ลงบนเฟรมภาพ
    annotated_frame = results[0].plot()

    # แสดงผล
    cv2.imshow("Detection Window", annotated_frame)

    # กด 'q' เพื่อออก
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()