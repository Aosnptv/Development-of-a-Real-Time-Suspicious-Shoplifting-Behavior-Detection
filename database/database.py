import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join("database", "shoplifting_detection.db")

def init_db():
    """สร้างตารางฐานข้อมูลและใส่ข้อมูลเริ่มต้นหากยังไม่มีไฟล์ฐานข้อมูล"""
    # ตรวจสอบและสร้างโฟลเดอร์ฐานข้อมูลก่อน
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. สร้างตาราง Incidents
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
    
    # 2. สร้างตาราง System Logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time TEXT,
            event TEXT
        )
    """)
    
    # ใส่ข้อมูลเริ่มต้นหากตารางยังว่างอยู่
    cursor.execute("SELECT COUNT(*) FROM incidents")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO incidents (time, camera, person, score, status, image) VALUES ('2026-07-13 10:45:12', 'Camera 01', 'PID-9482', 0.92, 'Unresolved', 'https://via.placeholder.com/150?text=Incident+1')")
        cursor.execute("INSERT INTO incidents (time, camera, person, score, status, image) VALUES ('2026-07-13 10:42:05', 'Camera 02', 'PID-1042', 0.88, 'Resolved', 'https://via.placeholder.com/150?text=Incident+2')")
        
    cursor.execute("SELECT COUNT(*) FROM system_logs")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO system_logs (time, event) VALUES ('10:01:12', 'System Started')")
        cursor.execute("INSERT INTO system_logs (time, event) VALUES ('10:02:45', 'Database Connected')")
        cursor.execute("INSERT INTO system_logs (time, event) VALUES ('10:03:20', 'Camera 1 Connected')")
        cursor.execute("INSERT INTO system_logs (time, event) VALUES ('10:05:00', 'Dashboard Ready')")
        
    conn.commit()
    conn.close()

def get_all_incidents():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT time, camera, person, score, status, image FROM incidents ORDER BY time DESC", conn)
    conn.close()
    return df

def get_recent_logs():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT time, event FROM system_logs ORDER BY id DESC LIMIT 10", conn)
    conn.close()
    return df