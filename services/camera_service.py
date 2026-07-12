import time

class CameraService:
    def __init__(self, camera_id: int, camera_source: str):
        self.camera_id = camera_id
        self.camera_source = camera_source
        self.is_connected = False
        self.fps = 0.0
        self.resolution = "N/A"

    def connect(self) -> bool:
        # Mocking Connection สำหรับรอบ 3.1
        self.is_connected = True
        self.fps = 30.0
        self.resolution = "1920x1080"
        return True

    def disconnect(self):
        self.is_connected = False
        self.fps = 0.0
        self.resolution = "N/A"

    def get_status(self) -> dict:
        return {
            "id": self.camera_id,
            "connected": self.is_connected,
            "fps": self.fps,
            "resolution": self.resolution
        }

    def get_frame(self):
        """ในรอบ 3.2 ตรงนี้จะคืนค่าภาพเฟรมล่าสุดจาก OpenCV Buffer"""
        # ปัจจุบันคืนค่า None ไปก่อน
        return None

    def get_fps(self) -> float:
        return self.fps