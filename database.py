import sqlite3
from datetime import datetime

DB_NAME = "shoplifting_detection.db"

def init_db():
    """สร้างฐานข้อมูลและตารางหากยังไม่มี"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            suspicion_score INTEGER,
            image_path TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_incident(score, image_path):
    """บันทึกเหตุการณ์เสี่ยงลงฐานข้อมูล"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO incidents (timestamp, suspicion_score, image_path, status)
        VALUES (?, ?, ?, ?)
    ''', (now, score, image_path, "แจ้งเตือนแล้ว"))
    conn.commit()
    conn.close()

def get_all_incidents():
    """ดึงข้อมูลประวัติทั้งหมด"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incidents ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")