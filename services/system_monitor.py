import psutil
import time
from datetime import datetime
from core.constants import CPU_WARNING_THRESHOLD, RAM_WARNING_THRESHOLD

class SystemMonitor:
    def __init__(self):
        # บันทึกเวลาที่ระบบเริ่มทำงานเพื่อคำนวณ Uptime
        self.start_time = time.time()

    def get_uptime_string(self) -> str:
        """คำนวณระยะเวลาที่ระบบเปิดใช้งานมาในรูปแบบ 00h 00m 00s"""
        uptime_seconds = int(time.time() - self.start_time)
        hours = uptime_seconds // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60
        return f"{hours:02d}h {minutes:02d}m {seconds:02d}s"

    def get_metrics(self) -> dict:
        """
        รวบรวมข้อมูล Hardware Metrics ล่าสุดของเครื่อง 
        ส่งกลับเป็น Dictionary ตามโครงสร้างที่ AppState ต้องการ
        """
        try:
            # ดึงค่า CPU แบบ Non-blocking (interval=None หรือ 0.0 เพื่อไม่ให้ UI หน่วงกระตุก)
            cpu_usage = psutil.cpu_percent(interval=None)
            
            # ดึงข้อมูล RAM
            ram_info = psutil.virtual_memory()
            ram_usage = ram_info.percent
            
            # ดึงข้อมูล Disk (ไดรฟ์ที่โปรเจกต์ตั้งอยู่)
            disk_info = psutil.disk_usage('/')
            disk_usage = disk_info.percent
            
            # ดึงค่า GPU (ส่งกลับเป็น 0.0 ชั่วคราวจนกว่าจะฝังโมเดล YOLO ใน Sprint ถัดไป)
            gpu_usage = 0.0
            
            # คำนวณความเร็ว Network คร่าวๆ (ความต่างของ Bytes ส่ง-รับ)
            net_io = psutil.net_io_counters()
            # แปลงเป็น MB แบบเข้าใจง่าย
            sent_mb = net_io.bytes_sent / (1024 * 1024)
            recv_mb = net_io.bytes_recv / (1024 * 1024)
            network_str = f"↑ {sent_mb:.1f}MB / ↓ {recv_mb:.1f}MB"
            
            # เวลาปัจจุบันบนระบบ
            current_time = datetime.now().strftime("%H:%M:%S")

            return {
                "cpu": cpu_usage,
                "ram": ram_usage,
                "gpu": gpu_usage,
                "disk": disk_usage,
                "network": network_str,
                "uptime": self.get_uptime_string(),
                "time": current_time
            }
            
        except Exception as e:
            # กรณีเกิดความผิดพลาด ให้ส่งค่า Default กลับไปเพื่อป้องกันบอร์ดพัง
            return {
                "cpu": 0.0,
                "ram": 0.0,
                "gpu": 0.0,
                "disk": 0.0,
                "network": "Error",
                "uptime": "00h 00m 00s",
                "time": "--:--:--"
            }