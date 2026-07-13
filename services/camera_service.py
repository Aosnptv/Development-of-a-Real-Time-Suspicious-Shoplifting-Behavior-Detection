# services/camera_service.py
import cv2
from PySide6.QtCore import QObject, Signal, QTimer

class CameraWorker(QObject):
    # ส่งสัญญาณภาพสด (Raw OpenCV BGR Frame) ออกไปให้ทุกหน้าจอพร้อมกัน
    frame_received = Signal(object)

    def __init__(self):
        super().__init__()
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self._read_frame)

    def start_camera(self):
        # เปิดกล้องและตั้งค่าระดับฮาร์ดแวร์เพียงรอบเดียว ป้องกันลูปเลนส์วิ่งซูม
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0) # 🔴 ปิด Auto Focus ป้องกันจอยืดหดเอง
        
        if not self.timer.isActive():
            self.timer.start(33)  # ควบคุมความเร็วประมาณ ~30 FPS

    def _read_frame(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.frame_received.emit(frame)

    def stop_camera(self):
        self.timer.stop()
        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None