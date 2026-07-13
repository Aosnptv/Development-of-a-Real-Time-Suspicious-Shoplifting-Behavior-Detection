# ui/gallery_page.py
import os
import subprocess
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QGridLayout, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class GalleryPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Top Bar
        header_layout = QHBoxLayout()
        title = QLabel("Incident History Log")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #f8fafc;")
        
        btn_open_folder = QPushButton("Open Storage Directory")
        btn_open_folder.setStyleSheet("""
            QPushButton { 
                background-color: #38bdf8; color: #0f172a; font-weight: bold; 
                padding: 8px 16px; border-radius: 6px; border: none; font-size: 12px;
            }
            QPushButton:hover { background-color: #0ea5e9; }
        """)
        btn_open_folder.clicked.connect(self._open_incident_folder)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(btn_open_folder)
        layout.addLayout(header_layout)
        
        # Grid Scroll Area (สไตล์ Album Matrix เรียงลงล่าง)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: transparent; border: none;")
        
        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        self.grid_gallery = QGridLayout(container)
        self.grid_gallery.setSpacing(16)
        self.grid_gallery.setContentsMargins(0, 0, 0, 0)
        
        # ข้อมูลเหตุการณ์จำลองเพื่อจัด Matrix
        mock_incidents = [
            ("2026-07-13 10:24:11", "Concealment", "#ef4444"),
            ("2026-07-12 15:45:02", "Suspicious", "#eab308"),
            ("2026-07-12 11:12:54", "Concealment", "#ef4444"),
            ("2026-07-10 09:05:33", "Suspicious", "#eab308"),
            ("2026-07-09 18:22:19", "Concealment", "#ef4444"),
            ("2026-07-09 14:11:02", "Suspicious", "#eab308"),
        ]
        
        # กำหนดความกว้างแถวละ 3-4 รูปเพื่อความเป็นระเบียบ
        columns_limit = 3
        
        for idx, (time_str, alert_type, color) in enumerate(mock_incidents):
            item_frame = QFrame()
            item_frame.setStyleSheet("background-color: #1e293b; border-radius: 8px; border: 1px solid #334155;")
            item_vbox = QVBoxLayout(item_frame)
            item_vbox.setContentsMargins(8, 8, 8, 8)
            
            # บล็อกรูปภาพ
            lbl_img_placeholder = QLabel("NO IMAGE THUMBNAIL")
            lbl_img_placeholder.setFixedSize(240, 150)
            lbl_img_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_img_placeholder.setStyleSheet("background-color: #020617; border-radius: 6px; color: #475569; font-size: 11px; font-weight: bold;")
            
            # ข้อมูลแสตมป์เวลาและสถานะเหตุการณ์
            lbl_time = QLabel(time_str)
            lbl_time.setStyleSheet("font-size: 11px; color: #94a3b8; font-family: 'Consolas';")
            
            lbl_status = QLabel(alert_type.upper())
            lbl_status.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {color}; font-family: 'Segoe UI';")
            
            item_vbox.addWidget(lbl_img_placeholder)
            item_vbox.addWidget(lbl_time)
            item_vbox.addWidget(lbl_status)
            
            # คำนวณพิกัดแถวและคอลัมน์ให้เรียงตัวลงแนวตั้งแบบอัตโนมัติ
            row = idx // columns_limit
            col = idx % columns_limit
            self.grid_gallery.addWidget(item_frame, row, col)
            
        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _open_incident_folder(self):
        target_path = os.path.join(os.path.expanduser("~"), "Documents")
        if not os.path.exists(target_path):
            os.makedirs(target_path)
        
        if os.name == 'nt':
            os.startfile(target_path)
        else:
            subprocess.Popen(['xdg-open', target_path])