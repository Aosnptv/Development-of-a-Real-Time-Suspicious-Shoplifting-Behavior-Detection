import threading
from typing import Dict, Any, List

class AppState:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """ Singleton Pattern การันตีว่ามีคลังข้อมูลชุดเดียวทั่วทั้งระบบ """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AppState, cls).__new__(cls)
                cls._instance._init_state()
            return cls._instance

    def _init_state(self):
        self._state_lock = threading.Lock()
        self.system_metrics: Dict[str, Any] = {"cpu": 0.0, "ram": 0.0, "disk": 0.0, "uptime": "00h 00m 00s"}
        self.camera_pool: Dict[str, Dict[str, Any]] = {}
        self.is_detector_running: bool = False  
        self.alerts_today: int = 0                  
        self.recent_alerts: List[Dict[str, Any]] = [] 

    @property
    def fps_average(self) -> float:
        """ 
        [Dynamic Property] คำนวณค่า FPS เฉลี่ยของกล้องทุกตัวที่ออนไลน์อยู่แบบ Real-time
        ถ้าไม่มีกล้องเปิดอยู่เลย จะส่งกลับเป็น 0.0 เพื่อป้องกันการหารด้วยศูนย์ (Division by Zero)
        """
        with self._state_lock:
            if not self.camera_pool:
                return 0.0
            
            total_fps = 0.0
            active_cameras = 0
            
            for cam_data in self.camera_pool.values():
                # ดึงค่า fps จาก Snapshot ของ CameraManager (เช็กความปลอดภัยของข้อมูลด้วย)
                if isinstance(cam_data, dict) and cam_data.get("online", False):
                    total_fps += float(cam_data.get("fps", 0.0))
                    active_cameras += 1
            
            if active_cameras == 0:
                return 0.0
                
            return round(total_fps / active_cameras, 1)

    def update_system_metrics(self, metrics: dict):
        with self._state_lock:
            self.system_metrics.update(metrics)

    def update_camera_pool(self, camera_key: str, data: dict):
        """ อัปเดตแพลตฟอร์มข้อมูลของกล้องรายตัว (Thread-safe) """
        with self._state_lock:
            self.camera_pool[camera_key] = data

    def set_detector_status(self, status: bool):
        """ สั่งเปิด หรือ ปิด ระบบตรวจจับพฤติกรรม """
        with self._state_lock:
            self.is_detector_running = status

    def toggle_detector_status(self):
        """ สลับสถานะระบบตรวจจับ """
        with self._state_lock:
            self.is_detector_running = not self.is_detector_running

    def increment_alert(self, alert_details: dict = None):
        """ เมื่อโมเดลเจอพฤติกรรมน่าสงสัย ให้สั่งบวกยอดสะสมและเก็บ Log """
        with self._state_lock:
            self.alerts_today += 1
            if alert_details:
                self.recent_alerts.insert(0, alert_details)
                if len(self.recent_alerts) > 50:
                    self.recent_alerts.pop()

    def reset_daily_alerts(self):
        """ ล้างแต้มแจ้งเตือนเมื่อขึ้นวันใหม่ """
        with self._state_lock:
            self.alerts_today = 0
            self.recent_alerts.clear()