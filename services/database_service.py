import sqlite3
import os
from datetime import datetime

class DatabaseService:
    def __init__(self, db_path="database.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """สร้างตารางเก็บข้อมูลประวัติ หากยังไม่มีในระบบ"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                camera_id INTEGER,
                person_id INTEGER,
                timestamp TEXT,
                image_path TEXT,
                status TEXT DEFAULT 'Unresolved'
            )
        """)
        conn.commit()
        conn.close()
        print("[DatabaseService] 💾 เชื่อมต่อฐานข้อมูล SQLite สำเร็จ!")

    def add_incident(self, camera_id, person_id, image_path):
        """บันทึกเหตุการณ์ต้องสงสัยขโมยของลงฐานข้อมูล"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # ดึงเวลาปัจจุบันในฟอร์แมตที่อ่านง่าย
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute("""
                INSERT INTO incidents (camera_id, person_id, timestamp, image_path, status)
                VALUES (?, ?, ?, ?, 'Unresolved')
            """, (camera_id, person_id, now_str, image_path))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[DatabaseService] ⚠️ เกิดข้อผิดพลาดในการเขียน DB: {e}")
            return False

    def get_all_incidents(self):
        """ดึงประวัติทั้งหมดเพื่อเอาไปแสดงบนหน้า UI Dashboard (History Log)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM incidents ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        return rows