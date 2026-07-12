import os

# ==============================================================================
# 📂 SYSTEM PATHS (ศูนย์รวมพิกัดโฟลเดอร์และไฟล์ทั้งหมดในระบบ)
# ==============================================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ที่ตั้งฐานข้อมูล SQLite
DB_PATH = os.path.join(BASE_DIR, "database", "system.db")

# ที่สำหรับบันทึก Log และค่าคอนฟิก (เพิ่ม CONFIG_PATH เข้าไปตรงนี้)
LOG_FILE_PATH = os.path.join(BASE_DIR, "logs", "system.log")
CONFIG_FILE_PATH = os.path.join(BASE_DIR, "config.json")
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")  # << เพิ่มตัวนี้เพื่อแก้ปัญหา ImportError ของ ConfigService

# ศูนย์จัดเก็บไฟล์มีเดียหลักฐานสำหรับระบุตัวตน (จาก Sprint 4.0 โครงสร้างใหม่)
STORAGE_IMAGE_DIR = os.path.join(BASE_DIR, "storage", "images")
STORAGE_VIDEO_DIR = os.path.join(BASE_DIR, "storage", "videos")
STORAGE_TEMP_DIR = os.path.join(BASE_DIR, "storage", "temp")


# ==============================================================================
# 📊 HARDWARE MONITOR THRESHOLDS (เกณฑ์ความปลอดภัยของฮาร์ดแวร์)
# ==============================================================================
CPU_WARNING_THRESHOLD = 75.0
CPU_CRITICAL_THRESHOLD = 90.0

RAM_WARNING_THRESHOLD = 80.0
RAM_CRITICAL_THRESHOLD = 95.0

DISK_WARNING_THRESHOLD = 85.0