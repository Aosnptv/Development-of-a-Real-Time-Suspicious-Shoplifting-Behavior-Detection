import os

class AIService:
    def __init__(self, model_path="models/shoplifting_yolov8.pt"):
        self.model_path = model_path
        self.model = None
        # เรียกใช้งานฟังก์ชันโหลดโมเดลตอนเริ่มต้น
        self.load_model()

    def load_model(self):
        """โหลดโมเดล AI อย่างปลอดภัย หากไม่มีไฟล์จะเข้าสู่ Simulation Mode"""
        print(f"[AIService] กำลังโหลดโมเดล YOLO จาก: {self.model_path}")
        try:
            # ตรวจสอบว่ามี ultralytics หรือไม่ ถ้ามีให้ทำการโหลด
            from ultralytics import YOLO
            if os.path.exists(self.model_path):
                self.model = YOLO(self.model_path)
                print("[AIService] 🟢 โหลดโมเดลสำเร็จ!")
            else:
                raise FileNotFoundError(f"ไม่พบไฟล์โมเดลที่ตำแหน่ง {self.model_path}")
        except Exception as e:
            print(f"[AIService] ⚠️ [ERROR] เกิดข้อผิดพลาดในการโหลดโมเดล: {e}")
            print("[AIService] ℹ️ เปลี่ยนเข้าสู่ระบบจำลอง (Simulation Mode) ชั่วคราว")
            self.model = None

    def predict(self, frame):
        """ฟังก์ชันทำนายผล (รองรับกรณีไม่มีโมเดล)"""
        if self.model is None:
            # คืนค่าเปล่ากรณีระบบอยู่ในโหมดจำลอง เพื่อป้องกันโปรแกรมหลักพัง
            return []
        return self.model(frame)