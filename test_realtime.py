import cv2
import os
from ultralytics import YOLO

def main():
    # 1. ตั้งค่าเลือกรุ่นโมเดล (ตรวจสอบ Path ให้ถูกต้อง)
    # หากย้ายไฟล์ไปที่โฟลเดอร์ models แล้วให้ใช้ "models/shoplifting_yolov8.pt"
    # แต่ถ้าจะดึงจากโฟลเดอร์ที่เพิ่งเทรนเสร็จสดๆ ร้อนๆ ให้ใช้ Path ด้านล่างนี้ได้เลยครับ:
    model_path = r"runs\detect\shoplifting_model_v1-5\weights\best.pt"
    
    if not os.path.exists(model_path):
        print(f"🔴 ไม่พบไฟล์โมเดลที่ตำแหน่ง: {model_path}")
        print("💡 กรุณาตรวจสอบ Path ของไฟล์ best.pt อีกครั้งครับ")
        return

    print(f"🧠 กำลังโหลดโมเดล AI จาก: {model_path} ...")
    model = YOLO(model_path)
    print("🟢 โหลดโมเดลสำเร็จ!")

    # 2. เปิดกล้องเว็บแคมโน้ตบุ๊ก (ใช้เลข 0 ตามที่คุยกันไว้)
    print("🎬 กำลังเปิดกล้องเว็บแคม (Index 0)...")
    cap = cv2.VideoCapture(0)

    # ตั้งค่าความละเอียดกล้อง (ถ้ากล้องรองรับ ช่วยให้ภาพคมชัดขึ้น)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    if not cap.isOpened():
        print("🔴 เปิดกล้องไม่ได้! กรุณาเช็คว่ามีโปรแกรมอื่น (เช่น Zoom, OBS) แย่งใช้กล้องอยู่หรือไม่")
        return

    print("\n-----------------------------------------------------")
    print("🚀 ระบบเริ่มทำงานแล้ว!")
    print("👉 เดินไปหน้ากล้อง ถือสินค้า หรือถือตะกร้า เพื่อทดสอบได้เลย")
    print("❌ กดปุ่ม 'q' บนคีย์บอร์ดเพื่อปิดหน้าต่างทดสอบ")
    print("-----------------------------------------------------\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠️ ไม่สามารถดึงภาพจากกล้องได้")
            break

        # 3. ส่งภาพให้ AI ประมวลผลตรวจจับคลาสทั้ง 4
        # (conf=0.40 คือเอาเฉพาะวัตถุที่มั่นใจเกิน 40% ขึ้นไป เพื่อลดกรอบมั่ว)
        results = model(frame, conf=0.40)

        # 4. ใช้คำสั่ง .plot() เพื่อวาดกรอบสี่เหลี่ยม ชื่อคลาส และเปอร์เซ็นต์ความมั่นใจ
        annotated_frame = results[0].plot()

        # 5. แสดงผลลัพธ์บนหน้าต่าง Pop-up
        cv2.imshow("YOLO11s Real-Time Detection Test", annotated_frame)

        # 6. ดักจับการกดปุ่ม 'q' เพื่อออกจากโปรแกรม
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # คืนหน่วยความจำเมื่อปิดโปรแกรม
    cap.release()
    cv2.destroyAllWindows()
    print("👋 ปิดระบบทดสอบเรียบร้อยครับ")

if __name__ == "__main__":
    main()