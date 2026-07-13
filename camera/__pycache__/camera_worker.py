# camera/camera_worker.py
import cv2
import time
from PySide6.QtCore import QThread, Signal
from core.app_state import AppState
from services.logger import logger

class CameraWorker(QThread):
    # สัญญาณแจ้งเตือนเมื่อมีเฟรมภาพใหม่เข้ามา (ส่งค่า FPS กลับไปแสดงผลด้วย)
    frame_received = Signal(float) 

    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self.running = True
        self.state = AppState()

    def run(self):
        logger.info(f"[Camera Thread] Starting Webcam Index: {self.camera_index}")
        cap = cv2.VideoCapture(self.camera_index)
        
        # ตั้งค่าขนาดบัฟเฟอร์ภายในตัวกล้องให้ต่ำสุด เพื่อให้ภาพไม่ดีเลย์ย้อนหลัง
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # ลองตั้งความละเอียดกล้อง (ปรับได้ตามความเหมาะสม)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        prev_time = 0
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                logger.warning("[Camera Thread] Failed to grab frame from Webcam.")
                self.state.camera_pool["Camera_0"]["online"] = False
                time.sleep(0.03) # พักรอบป้องกันเธรดทำงานหนักเกินไป
                continue

            # คำนวณค่า FPS แบบเรียลไทม์
            current_time = time.time()
            fps = 1.0 / (current_time - prev_time) if prev_time > 0 else 0.0
            prev_time = current_time

            # 🟢 อัปเดตเฟรมดิบลงบัฟเฟอร์ใน AppState โดยตรง
            self.state.camera_pool["Camera_0"]["online"] = True
            self.state.camera_pool["Camera_0"]["frame"] = frame
            self.state.fps_average = round(fps, 1)

            # ยิงสัญญาณแจ้งเตือน UI Thread ว่ามีของใหม่มาส่งแล้วนะ
            self.frame_received.emit(fps)
            
            # หน่วงเวลาเล็กน้อยเพื่อให้กล้องดึงภาพสัมพันธ์กับความเร็วตัวฮาร์ดแวร์ (~30 FPS)
            time.sleep(0.01)

        cap.release()
        self.state.camera_pool["Camera_0"]["online"] = False
        logger.info("[Camera Thread] Webcam thread stopped safely.")

    def stop(self):
        self.running = False
        self.wait()