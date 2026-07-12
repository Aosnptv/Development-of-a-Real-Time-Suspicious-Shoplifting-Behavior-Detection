import threading
from typing import Callable, Dict, List
import services.logger as logger # เชื่อมตรงเข้าระบบ Logger กลาง

class EventBus:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(EventBus, cls).__new__(cls)
                cls._instance._listeners = {}
        return cls._instance

    def subscribe(self, event_type: str, listener: Callable):
        """ให้ Service ต่างๆ มาลงทะเบียนรอฟังข่าวสารชนิดที่สนใจ"""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)

    def publish(self, event_type: str, data: dict = None):
        """เมื่อเกิดเหตุการณ์ ให้กระจายข่าวสารออกไปให้ทุกโมดูลที่รอฟังทันที"""
        if data is None:
            data = {}
            
        # บันทึกลงไฟล์ log หลักอัตโนมัติทุกครั้งที่มีความเคลื่อนไหวผ่าน Event Bus
        if "message" in data:
            logger.log_event(f"[{event_type.upper()}] {data['message']}")
            
        if event_type in self._listeners:
            for listener in self._listeners[event_type]:
                # รันงานของแต่ละผู้ฟังแยกกัน (สามารถประยุกต์ใช้ Threading ในอนาคตได้)
                try:
                    listener(data)
                except Exception as e:
                    logger.log_event(f"Error in listener for {event_type}: {str(e)}")

# ตัวแปร Global สำหรับเรียกใช้งานทั่วทั้งโปรเจกต์
event_bus = EventBus()