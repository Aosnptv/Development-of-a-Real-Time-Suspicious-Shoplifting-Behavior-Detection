import os
import datetime

class Logger:
    def __init__(self, log_file_path="logs/system.log"):
        self.log_file_path = log_file_path
        os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)

    def _write_log(self, level: str, message: str):
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"{current_time} [{level}] {message}\n"
        with open(self.log_file_path, "a", encoding="utf-8") as f:
            f.write(log_line)

    def info(self, message: str):
        self._write_log("INFO", message)

    def warning(self, message: str):
        self._write_log("WARNING", message)

    def error(self, message: str):
        self._write_log("ERROR", message)

    def get_recent_logs(self, limit=10) -> list:
        if not os.path.exists(self.log_file_path):
            return []
        
        with open(self.log_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        parsed_logs = []
        for line in lines[-limit:]:
            if " [" in line and "] " in line:
                # แยกวันเวลา, เลเวล และข้อความออกจากกัน
                parts = line.split(" [", 1)
                time_str = parts[0].strip()
                level_msg = parts[1].split("] ", 1)
                level = level_msg[0].strip()
                msg = level_msg[1].strip()
                parsed_logs.append({"Time": time_str, "Level": level, "Event": msg})
                
        return parsed_logs[::-1]

# Instance หลักสำหรับเรียกใช้งานทั่วทั้งโปรเจกต์
logger = Logger()