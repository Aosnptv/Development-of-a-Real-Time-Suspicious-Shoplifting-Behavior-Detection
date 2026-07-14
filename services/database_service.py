import sqlite3
import os
import pandas as pd
from datetime import datetime
from services.logger_service import get_logger
from services.config_service import ConfigManager


class DatabaseService:
    def __init__(self):
        self.logger = get_logger("DatabaseService")
        self.config = ConfigManager()
        
        # ดึงชื่อไฟล์ฐานข้อมูลจาก Config (ถ้าไม่มีให้ใช้ค่าเริ่มต้น)
        self.db_path = self.config.get("database.path", "data/alerts_history.db")
        
        # ตรวจสอบและสร้างโฟลเดอร์ data/ ถ้ายังไม่มี
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self._create_tables()

    def _get_connection(self):
        """สร้างการเชื่อมต่อกับ SQLite"""
        return sqlite3.connect(self.db_path)

    def _create_tables(self):
        """สร้างตารางสำหรับเก็บประวัติการแจ้งเตือน หากยังไม่มีตารางนี้"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS detection_alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        camera_id TEXT NOT NULL,
                        behavior_type TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        image_path TEXT,
                        is_reviewed BOOLEAN DEFAULT 0
                    )
                """)
                conn.commit()
                self.logger.info("ตรวจสอบ/สร้างตารางฐานข้อมูลสำเร็จ")
        except Exception as e:
            self.logger.error(f"เกิดข้อผิดพลาดในการสร้างฐานข้อมูล: {e}")

    def log_alert(self, camera_id, behavior_type, confidence, image_path=""):
        """บันทึกเหตุการณ์ใหม่ลงฐานข้อมูล"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO detection_alerts (camera_id, behavior_type, confidence, image_path)
                    VALUES (?, ?, ?, ?)
                """, (camera_id, behavior_type, confidence, image_path))
                conn.commit()
                self.logger.info(f"บันทึก Alert: {behavior_type} จาก {camera_id} (แม่นยำ {confidence:.2f})")
                return cursor.lastrowid
        except Exception as e:
            self.logger.error(f"ไม่สามารถบันทึก Alert ได้: {e}")
            return None

    def get_recent_alerts(self, limit=50):
        """ดึงข้อมูลแจ้งเตือนล่าสุดไปโชว์ที่หน้า Playback หรือ Dashboard"""
        try:
            with self._get_connection() as conn:
                query = f"""
                    SELECT id, timestamp, camera_id, behavior_type, confidence, image_path 
                    FROM detection_alerts 
                    ORDER BY timestamp DESC LIMIT {limit}
                """
                # ใช้ Pandas ดึงข้อมูลมาเป็น DataFrame เพื่อให้เอาไปใช้ต่อในตาราง UI ได้ง่าย
                df = pd.read_sql_query(query, conn)
                return df
        except Exception as e:
            self.logger.error(f"ดึงข้อมูล Alerts ผิดพลาด: {e}")
            return pd.DataFrame()

    def export_to_csv(self, export_path="data/export_alerts.csv"):
        """ส่งออกประวัติทั้งหมดเป็นไฟล์ CSV (สำหรับทำรายงาน)"""
        try:
            with self._get_connection() as conn:
                df = pd.read_sql_query("SELECT * FROM detection_alerts", conn)
                df.to_csv(export_path, index=False, encoding='utf-8')
                self.logger.info(f"ส่งออกข้อมูล CSV ไปที่ {export_path} สำเร็จ")
                return True
        except Exception as e:
            self.logger.error(f"ส่งออก CSV ผิดพลาด: {e}")
            return False