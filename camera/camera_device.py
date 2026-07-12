import cv2
import time
import numpy as np
from typing import Tuple, Optional

class CameraDevice:
    def __init__(self, source):
        self.source = source
        self.cap = None
        self.width = 0
        self.height = 0
        self.actual_fps = 0.0
        self.is_running = False
        self._prev_time = 0.0

    def open_hardware(self) -> bool:
        """เกาะสัญญาณกับตัวกล้องและอ่านความละเอียดจริงของอุปกรณ์"""
        if str(self.source).isdigit():
            self.cap = cv2.VideoCapture(int(self.source), cv2.CAP_DSHOW) # โหมดความเร็วสูงสำหรับ Windows
        else:
            self.cap = cv2.VideoCapture(self.source)

        if not self.cap.isOpened():
            return False

        # อ่านค่าความละเอียดจริงจากตัวกล้อง
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) if hasattr(cv2, 'CAP_PROP_FRAME_WIDTH') else 640
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) if hasattr(cv2, 'CAP_PROP_FRAME_HEIGHT') else 480
        
        self.is_running = True
        self._prev_time = time.time()
        return True

    def grab_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """ดึงเฟรมภาพดิบพร้อมคำนวณค่า FPS ผันแปรตามความจริง"""
        if not self.is_running or self.cap is None:
            return False, None

        ret, frame = self.cap.read()
        if not ret or frame is None:
            return False, None

        # คำนวณความเร็วเฟรมเรตจริงของตัวกล้อง ณ เสี้ยววินาทีนั้น
        current_time = time.time()
        duration = current_time - self._prev_time
        if duration > 0:
            current_fps = 1.0 / duration
            # ใช้ Exponential Moving Average (EMA) เพื่อไม่ให้ตัวเลข FPS แกว่งจนอ่านไม่รู้เรื่อง
            self.actual_fps = (self.actual_fps * 0.9) + (current_fps * 0.1)
        self._prev_time = current_time

        return True, frame

    def close_hardware(self):
        """ปล่อยอุปกรณ์คืนระบบปฏิบัติการ ป้องกันปัญหา Memory Leak หรือกล้องค้าง"""
        self.is_running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None