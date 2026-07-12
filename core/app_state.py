import threading

class AppState:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AppState, cls).__new__(cls)
                cls._instance._init_state()  # เรียกฟังก์ชันตั้งต้นค่าภายในคลาส
        return cls._instance

    def _init_state(self):
        """กำหนดค่าเริ่มต้นให้กับสถานะของแอปพลิเคชัน (เรียกครั้งแรกครั้งเดียว)"""
        self.lock = threading.Lock()
        
        # รวบรวมสถานะฮาร์ดแวร์จริงของเครื่อง
        self.system_metrics = {
            "cpu": 0.0, 
            "ram": 0.0, 
            "gpu": 0.0, 
            "disk": 0.0,
            "network": "↑ 0.0MB / ↓ 0.0MB", 
            "uptime": "00h 00m 00s", 
            "time": ""
        }
        
        # เมทริกซ์การรันระบบ AI และภาพรวม
        self.fps_average = 0.0
        self.alerts_today = 0
        self.persons_detected = 0
        
        # แฟล็กตรวจสอบสถานะระบบย่อย
        self.is_db_connected = True
        self.is_telegram_connected = False
        self.is_detector_running = False
        
        # คลังจัดเก็บข้อมูลและเฟรมภาพของกล้องทุกตัวสำหรับ Sprint 4
        self.camera_pool = {}

    def update_system_metrics(self, metrics_dict: dict):
        with self.lock:
            self.system_metrics = metrics_dict

    def update_camera_pool(self, cam_name: str, cam_data: dict):
        """รับข้อมูลสถานะล่าสุดรวมถึงเฟรมภาพของกล้องแต่ละตัวจาก CameraManager"""
        with self.lock:
            self.camera_pool[cam_name] = cam_data