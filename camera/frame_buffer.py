import threading
import numpy as np
from typing import Optional

class FrameBuffer:
    def __init__(self):
        self._latest_frame: Optional[np.ndarray] = None
        self._lock = threading.Lock()
        
        # ตัวชี้วัดสำหรับหน้าวินิจฉัย (Diagnostics Metrics)
        self.frame_count = 0
        self.dropped_frame_count = 0

    def set_frame(self, frame: np.ndarray):
        """รับเฟรมใหม่เข้ามาทับตัวเก่าในหน่วยความจำทันที (Thread-safe)"""
        with self._lock:
            if frame is not None:
                self._latest_frame = frame.copy()
                self.frame_count += 1
            else:
                self.dropped_frame_count += 1

    def get_latest_frame(self) -> Optional[np.ndarray]:
        """คืนเฟรมล่าสุดออกไปให้คนนำไปใช้งาน (Dashboard / YOLO)"""
        with self._lock:
            return self._latest_frame

    def reset(self):
        """เคลียร์สถานะตัวนับเฟรมทั้งหมด"""
        with self._lock:
            self._latest_frame = None
            self.frame_count = 0
            self.dropped_frame_count = 0