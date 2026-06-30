import sqlite3
from datetime import datetime

DB_NAME = "shoplifting_detection.db"

def init_db():
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
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO incidents (timestamp, suspicion_score, image_path, status)
        VALUES (?, ?, ?, ?)
    ''', (now, score, image_path, "ตรวจพบการซ่อนสินค้า"))
    conn.commit()
    conn.close()

def get_all_incidents():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incidents ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_dashboard_stats():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM incidents")
    total_alerts = cursor.fetchone()[0]
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(*) FROM incidents WHERE timestamp LIKE ?", (f"{today_str}%",))
    today_alerts = cursor.fetchone()[0]
    
    conn.close()
    return total_alerts, today_alerts