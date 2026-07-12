import threading

class FrameBuffer:
    def __init__(self):
        self.lock = threading.Lock()
        self.frame = None

    def push(self, frame):
        """ฝั่งอ่านภาพโยนเฟรมล่าสุดเข้ามาที่นี่ (เขียนทับเฟรมเก่าทันที)"""
        with self.lock:
            self.frame = frame

    def pop(self):
        """ฝั่ง UI หรือ AI ดึงภาพสดใหม่ล่าสุดไปแสดงผล"""
        with self.lock:
            return self.frame