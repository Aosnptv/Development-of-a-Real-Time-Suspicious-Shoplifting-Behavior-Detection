import sys
import os

# มั่นใจว่าอ่านโฟลเดอร์ในโปรเจกต์ออก
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from services.logger import logger

def main():
    logger.info("============== STARTING APPLICATION ==============")
    app = QApplication(sys.argv)
    
    # รันหน้าต่างหลัก (เธรดกล้องถูกเรียกเปิดอัตโนมัติจากข้างในหน้าแดชบอร์ดแล้ว)
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()