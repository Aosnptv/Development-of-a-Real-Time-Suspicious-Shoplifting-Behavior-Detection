from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class MetricWidget(QFrame):
    def __init__(self, label: str, initial_value: str, unit: str = ""):
        super().__init__()
        self.setObjectName("MetricCard")
        self.unit = unit
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)
        
        # ข้อความหัวการ์ด
        self.lbl_title = QLabel(label.upper())
        self.lbl_title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.lbl_title.setStyleSheet("color: #8892b0;")
        
        # ตัวเลขชี้วัดหลัก
        self.lbl_value = QLabel(f"{initial_value} {self.unit}".strip())
        self.lbl_value.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        self.lbl_value.setStyleSheet("color: #ffffff;")
        self.lbl_value.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_value)
        
        self.setStyleSheet("""
            #MetricCard {
                background-color: #162447;
                border: 1px solid #1f4068;
                border-radius: 8px;
            }
        """)
        
    def update_value(self, new_value: str):
        """ฟังก์ชันสำหรับสั่งอัปเดตตัวเลขสดบนหน้าจอ"""
        self.lbl_value.setText(f"{new_value} {self.unit}".strip())