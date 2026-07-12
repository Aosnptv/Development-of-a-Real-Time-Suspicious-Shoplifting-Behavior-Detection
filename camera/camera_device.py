import cv2
import threading
import time
import datetime
from camera.camera_buffer import FrameBuffer
from camera.frame_processor import FrameProcessor
from services.logger import logger

class CameraDevice:
    def __init__(self, cam_id: int, name: str, source: str):
        self.cam_id = cam_id
        self.name = name
        self.source = source
        
        #แปลงค่า source เป็นตัวเลขกรณีที่เป็น Webcam ในเครื่อง
        try:
            self.source = int(source)
        except ValueError:
            self.source = source
            
        self.buffer = FrameBuffer()
        self.is_running = False
        self.thread = None
        self.fps = 0.0
        self.resolution = "N/A"
        
    def start(self):
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
            logger.info(f"Started worker thread for camera: {self.name}")

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        logger.info(f"Stopped worker thread for camera: {self.name}")

    def _capture_loop(self):
        # เปิดการเชื่อมต่อสตรีมกล้อง
        cap = cv2.VideoCapture(self.source)
        if not cap.isOpened():
            logger.error(f"Failed to open video source for {self.name}: {self.source}")
            self.is_running = False
            return

        # ตรวจสอบขนาดความละเอียดภาพดั้งเดิม
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.resolution = f"{width}x{height}"

        prev_time = 0
        while self.is_running:
            ret, frame = cap.read()
            if not ret:
                logger.warning(f"Failed to grab frame from {self.name}. Reconnecting...")
                time.sleep(1.0)
                continue

            # ประมวลผลภาพขั้นต้น (Resize + Timestamp)
            processed_frame = FrameProcessor.process(frame)
            self.buffer.push(processed_frame)

            # คำนวณ FPS จริงของฮาร์ดแวร์กล้อง
            current_time = time.time()
            self.fps = 1 / (current_time - prev_time) if prev_time > 0 else 30.0
            prev_time = current_time
            
        cap.release()

    def get_latest_frame(self):
        return self.buffer.pop()

    def get_status_report(self) -> dict:
        return {
            "online": self.is_running,
            "fps": round(self.fps, 1),
            "resolution": self.resolution,
            "last_seen": datetime.datetime.now().strftime("%H:%M:%S") if self.is_running else "N/A"
        }