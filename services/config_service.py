import json
import os
from core.constants import CONFIG_PATH

class ConfigService:
    def __init__(self):
        self.config_path = CONFIG_PATH
        self._ensure_config_exists()

    def _ensure_config_exists(self):
        """ถ้ายังไม่มีไฟล์ config.json ให้สร้างไฟล์เริ่มต้นขึ้นมา"""
        if not os.path.exists(self.config_path):
            default_config = {
                "model": "yolo11s.pt",
                "tracker": "ByteTrack",
                "confidence": 0.35,
                "iou": 0.45,
                "camera": {
                    "camera_1": "0",
                    "camera_2": "rtsp://192.168.1.50/stream1"
                },
                "telegram": {
                    "enabled": False,
                    "token": "",
                    "chat_id": ""
                }
            }
            self.save_config(default_config)

    def load_config(self) -> dict:
        with open(self.config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_config(self, config_data: dict):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)

    def get_value(self, key_path: str, default=None):
        """ดึงค่าคอนฟิกแบบระบุพาธย่อย เช่น get_value('telegram.enabled')"""
        config = self.load_config()
        try:
            keys = key_path.split('.')
            val = config
            for k in keys:
                val = val[k]
            return val
        except KeyError:
            return default