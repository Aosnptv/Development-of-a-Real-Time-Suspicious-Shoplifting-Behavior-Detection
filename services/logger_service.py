import logging
from logging.handlers import RotatingFileHandler
import os
from services.config_service import ConfigManager

def get_logger(name):
    "สร้างและตั้งค่า Logger สำหรับแต่ละโมดูล"
    # 1. โหลดการตั้งค่าว่าต้องการ Log ระดับไหน (INFO, DEBUG, ERROR)
    config = ConfigManager()
    log_level_str = config.get("logging.level", "INFO").upper()
    
    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    log_level = levels.get(log_level_str, logging.INFO)

    # 2. สร้าง Logger
    logger = logging.getLogger(name)
    
    # ป้องกันการแอด Handler ซ้ำเวลาดึงไปใช้หลายไฟล์
    if not logger.handlers:
        logger.setLevel(log_level)
        
        # สร้างโฟลเดอร์ logs อัตโนมัติถ้ายังไม่มี
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # กำหนดหน้าตาของ Log (เช่น [2026-07-15 12:00:00] [INFO] [CameraWorker] - เริ่มต้นกล้อง 1)
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Handler 1: ปริ้นท์ออก Console (หน้าจอดำ)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        # Handler 2: บันทึกลงไฟล์ app.log (หมุนเวียนไฟล์ละ 5MB สูงสุด 3 ไฟล์)
        max_bytes = config.get("logging.max_bytes", 5242880)
        backup_count = config.get("logging.backup_count", 3)
        
        file_handler = RotatingFileHandler(
            'logs/app.log', 
            maxBytes=max_bytes, 
            backupCount=backup_count, 
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger