from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QTableWidget, QTableWidgetItem, QHeaderView, 
                               QAbstractItemView, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
import os
from services.database_service import DatabaseService

class PlaybackPage(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DatabaseService()
        self.is_dark_theme = True
        self.setup_ui()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # ==========================================
        # ฝั่งซ้าย: ตารางประวัติการแจ้งเตือน
        # ==========================================
        left_layout = QVBoxLayout()
        
        self.lbl_title = QLabel("📋 ประวัติการตรวจพบพฤติกรรมต้องสงสัย")
        self.lbl_title.setStyleSheet("font-size: 20px; font-weight: bold;")
        left_layout.addWidget(self.lbl_title)

        # สร้างตาราง
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["เวลา", "กล้อง", "พฤติกรรม", "ความแม่นยำ"])
        
        # ตั้งค่าพฤติกรรมตาราง
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.show_evidence_image)
        
        left_layout.addWidget(self.table)
        main_layout.addLayout(left_layout, stretch=6)

        # ==========================================
        # ฝั่งขวา: แสดงภาพหลักฐาน
        # ==========================================
        right_layout = QVBoxLayout()
        
        self.lbl_preview_title = QLabel("📷 ภาพหลักฐาน")
        self.lbl_preview_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.lbl_preview_title.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.lbl_preview_title)

        # กรอบใส่รูปภาพ
        self.lbl_image = QLabel("คลิกที่รายการในตารางเพื่อดูภาพหลักฐาน")
        self.lbl_image.setAlignment(Qt.AlignCenter)
        self.lbl_image.setFrameShape(QFrame.Box)
        self.lbl_image.setMinimumSize(400, 300)
        self.lbl_image.setStyleSheet("background-color: #0f172a; color: #94a3b8;")
        
        right_layout.addWidget(self.lbl_image)
        right_layout.addStretch()
        
        main_layout.addLayout(right_layout, stretch=4)

    def load_data(self):
        """โหลดข้อมูลจากฐานข้อมูลมาแสดงในตาราง"""
        # ดึงข้อมูล 50 รายการล่าสุด
        df = self.db.get_recent_alerts(limit=50)
        
        self.table.setRowCount(0)
        if df.empty:
            return

        self.table.setRowCount(len(df))
        
        for row, data in df.iterrows():
            # คอลัมน์ 0: เวลา
            time_item = QTableWidgetItem(str(data['timestamp']))
            # คอลัมน์ 1: กล้อง
            cam_item = QTableWidgetItem(str(data['camera_id']))
            # คอลัมน์ 2: พฤติกรรม
            behavior_item = QTableWidgetItem(str(data['behavior_type']))
            # คอลัมน์ 3: ความแม่นยำ (แปลงเป็น %)
            conf_percent = float(data['confidence']) * 100
            conf_item = QTableWidgetItem(f"{conf_percent:.1f}%")
            
            # เก็บ path รูปภาพไว้ใน Item แบบลับๆ (UserData) เพื่อเอาไว้ดึงมาโชว์ตอนคลิก
            time_item.setData(Qt.UserRole, str(data['image_path']))

            self.table.setItem(row, 0, time_item)
            self.table.setItem(row, 1, cam_item)
            self.table.setItem(row, 2, behavior_item)
            self.table.setItem(row, 3, conf_item)

    def show_evidence_image(self):
        """แสดงรูปภาพเมื่อผู้ใช้คลิกเลือกแถวในตาราง"""
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            return
            
        # ดึง Path รูปภาพที่เราซ่อนไว้ในคอลัมน์แรก (เวลา)
        image_path = self.table.item(selected_rows[0].row(), 0).data(Qt.UserRole)
        
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            # ย่อรูปให้พอดีกับกรอบ โดยรักษาสัดส่วนไว้
            scaled_pixmap = pixmap.scaled(self.lbl_image.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.lbl_image.setPixmap(scaled_pixmap)
        else:
            self.lbl_image.clear()
            self.lbl_image.setText("❌ ไม่พบไฟล์ภาพหลักฐาน")

    def set_theme(self, is_dark_mode):
        """เปลี่ยนสีตามธีมของโปรแกรม"""
        self.is_dark_theme = is_dark_mode
        text_color = "white" if is_dark_mode else "black"
        bg_color = "#1e293b" if is_dark_mode else "#ffffff"
        table_bg = "#0f172a" if is_dark_mode else "#f8fafc"
        grid_color = "#334155" if is_dark_mode else "#e2e8f0"

        self.lbl_title.setStyleSheet(f"color: {text_color}; font-size: 20px; font-weight: bold;")
        self.lbl_preview_title.setStyleSheet(f"color: {text_color}; font-size: 18px; font-weight: bold;")
        
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {table_bg};
                color: {text_color};
                gridline-color: {grid_color};
                border: 1px solid {grid_color};
                border-radius: 8px;
            }}
            QHeaderView::section {{
                background-color: {bg_color};
                color: {text_color};
                padding: 4px;
                border: 1px solid {grid_color};
                font-weight: bold;
            }}
        """)
        
        if not self.lbl_image.pixmap():
            img_bg = "#0f172a" if is_dark_mode else "#f1f5f9"
            self.lbl_image.setStyleSheet(f"background-color: {img_bg}; color: {text_color}; border: 1px solid {grid_color};")