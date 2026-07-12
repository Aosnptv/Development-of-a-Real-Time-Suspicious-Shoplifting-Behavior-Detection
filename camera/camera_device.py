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
        self.fps = 0.0
        self.is_running = False
        
        # สำหรับคำนวณ FPS จริงแบบ Dynamic
        self._prev_time = 0.0

    def open(self) -> bool:
        """เปิดฮาร์ดแวร์กล้องและดึงข้อมูลทางกายภาพจริง"""
        # ปรับค่าอิงตามชนิดของ Source เพื่อป้องกัน OpenCV บล็อกเธรดนานเกินไป
        if str(self.source).isdigit():
            self.cap = cv2.VideoCapture(int(self.source), cv2.CAP_DSHOW) # สำหรับ Windows (ลดอาการกล้องเปิดช้า)
        else:
            self.cap = cv2.VideoCapture(self.source)

        if not self.cap.isOpened():
            return False

        # อ่านข้อมูลความละเอียดที่กล้องส่งมาจริง (DoD ข้อ 5) - แก้ไขจาก cv3 เป็น cv2 แล้ว
# ตรวจสอบและแก้ไขให้เป็น cv2 ทั้งสองบรรทัดครับ
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) if hasattr(cv2, 'CAP_PROP_FRAME_WIDTH') else int(self.cap.get(3))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) if hasattr(cv2, 'CAP_PROP_FRAME_HEIGHT') else int(self.cap.get(4))
        
        self.is_running = True
        self._prev_time = time.time()
        return True

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """อ่านเฟรมและคำนวณ Dynamic FPS จริง (DoD ข้อ 4)"""
        if not self.is_running or self.cap is None:
            return False, None

        ret, frame = self.cap.read()
        if not ret or frame is None:
            return False, None

        # คำนวณความเร็วเฟรมเรตผันแปรตามเวลาจริง
        current_time = time.time()
        time_diff = current_time - self._prev_time
        if time_diff > 0:
            actual_fps = 1.0 / time_diff
            # ใช้ Exponential Moving Average เพื่อให้ตัวเลข FPS นิ่งขึ้นเล็กน้อย ไม่แกว่งรุนแรงเกินไป
            self.fps = (self.fps * 0.9) + (actual_fps * 0.1)
        self._prev_time = current_time

        return True, frame

    def release(self):
        """คืนทรัพยากรกล้องให้ระบบปฏิบัติการ ป้องกัน Memory Leak (DoD ข้อ 11)"""
        self.is_running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None