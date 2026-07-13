# core/app_state.py
class AppState:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        # คลังเก็บสถานะกล้องสดและ Buffer เฟรมภาพ
        self.camera_pool = {
            "Camera_0": {
                "online": False,
                "frame": None
            }
        }
        
        # ตัวแปรระบบอื่น ๆ
        self.alerts_today = 0
        self.fps_average = 0.0
        self.is_detector_running = False
        self.system_metrics = {
            "cpu": 0.0,
            "ram": 0.0,
            "disk": 0.0,
            "uptime": "00:00:00"
        }
        self.model_threshold = 0.50
        self.telegram_token = ""
        self.telegram_chat_id = ""