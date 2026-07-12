import threading
import numpy as np
from typing import Optional

class FrameBuffer:
    def __init__(self):
        self._frame: Optional[np.ndarray] = None
        self._lock = threading.Lock()
        self.frame_count = 0
        self.dropped_frames = 0

    def set_frame(self, frame: np.ndarray):
        """อัปเดตเฟรมล่าสุดเข้าไปในคลัง (Thread-safe)"""
        with self._lock:
            if frame is not None:
                self._frame = frame.copy()
                self.frame_count += 1
            else:
                self.dropped_frames += 1

    def get_frame(self) -> Optional[np.ndarray]:
        """ดึงเฟรมล่าสุดออกไปใช้งาน"""
        with self._lock:
            return self._frame

    def reset(self):
        """ล้างสถานะตัวนับเฟรม"""
        with self._lock:
            self._frame = None
            self.frame_count = 0
            self.dropped_frames = 0