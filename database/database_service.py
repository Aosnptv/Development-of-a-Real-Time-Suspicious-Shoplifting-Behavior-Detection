import sqlite3
import os
from core.constants import DB_PATH
from services.logger import logger

class DatabaseService:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.init_db()

    def connect(self):
        """สร้างการเชื่อมต่อกับ SQLite Database"""
        return sqlite3.connect(self.db_path)

    def init_db(self):
        """สร้างตารางที่จำเป็นทั้งหมดหากยังไม่มีในระบบ"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = self.connect()
        cursor = conn.cursor()
        
        # 1. ตารางเก็บบันทึกเหตุการณ์ขโมย (Incidents Log)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time TEXT, 
                camera TEXT, 
                person TEXT, 
                score REAL, 
                status TEXT, 
                image TEXT
            )
        """)
        
        # 2. ตารางสำหรับบริหารจัดการกล้อง (Camera Inventory)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cameras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                source TEXT,
                status TEXT DEFAULT 'OFFLINE',
                resolution TEXT DEFAULT 'N/A',
                fps REAL DEFAULT 0.0,
                last_seen TEXT
            )
        """)
        
        # เพิ่มกล้องตัวอย่างเริ่มต้นกรณีฐานข้อมูลเพิ่งถูกสร้างใหม่
        cursor.execute("SELECT COUNT(*) FROM cameras")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO cameras (name, source, status) VALUES (?, ?, ?)", ("Camera 01", "0", "OFFLINE"))
            cursor.execute("INSERT INTO cameras (name, source, status) VALUES (?, ?, ?)", ("Camera 02", "demo.mp4", "OFFLINE"))
            logger.info("Database initialized with default camera profiles.")
            
        conn.commit()
        conn.close()

    def get_all_cameras(self) -> list:
        """ดึงรายชื่อกล้องทั้งหมดจาก Database ออกมาใช้งาน"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, source, status, resolution, fps, last_seen FROM cameras")
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": r[0], 
                "name": r[1], 
                "source": r[2], 
                "status": r[3], 
                "resolution": r[4], 
                "fps": r[5], 
                "last_seen": r[6]
            } for r in rows
        ]

    def add_camera(self, name: str, source: str):
        """เพิ่มกล้องตัวใหม่เข้าสู่ตารางฐานข้อมูล"""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO cameras (name, source) VALUES (?, ?)", (name, source))
            conn.commit()
            logger.info(f"Successfully inserted new camera '{name}' into database.")
        except sqlite3.IntegrityError:
            logger.warning(f"Failed to add camera '{name}': Name already exists.")
        finally:
            conn.close()

    def delete_camera(self, cam_id: int):
        """ลบกล้องออกจากระบบด้วย ID"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cameras WHERE id = ?", (cam_id,))
        conn.commit()
        conn.close()
        logger.info(f"Deleted camera ID {cam_id} from database.")