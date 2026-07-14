import json
import os

class ConfigManager:
    _instance = None

    def __new__(cls, config_file='config.json'):
        # ตรวจสอบว่ามีการโหลด Config ไปแล้วหรือยัง (Singleton Pattern)
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.config_file = config_file
            cls._instance.config = {}
            cls._instance.load_config()
        return cls._instance

    def load_config(self):
        "โหลดข้อมูลจากไฟล์ JSON"
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            # ถ้าหาไฟล์ไม่เจอ ให้ใช้ค่าเริ่มต้นและสร้างไฟล์ให้เลย
            self.config = self.create_default_config()
            self.save_config()

    def create_default_config(self):
        "ค่าเริ่มต้นของระบบเผื่อไฟล์หาย"
        return {
            "app_name": "Shoplifting Detection System",
            "camera": {"cam_1": 0},
            "ai": {"model_path": "models/shoplifting_yolov8.pt", "confidence_threshold": 0.65},
            "telegram": {"enabled": False, "bot_token": "", "chat_id": ""},
            "logging": {"level": "INFO"}
        }

    def save_config(self):
        "บันทึกการตั้งค่ากลับลงไฟล์ JSON"
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def get(self, key_path, default=None):
        """
        ดึงค่าจาก Config แบบเจาะลึก 
        ตัวอย่างการใช้: config.get('ai.confidence_threshold')
        """
        keys = key_path.split('.')
        val = self.config
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val