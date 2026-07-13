# ui/playback_page.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QTableWidget, QTableWidgetItem, 
                               QPushButton, QDateEdit, QHeaderView)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont

class PlaybackPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #f8fafc;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # ─────────────── HEADER & FILTER AREA ───────────────
        filter_frame = QFrame()
        filter_frame.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(16, 16, 16, 16)
        
        title_lbl = QLabel("⏪ PLAYBACK HISTORY")
        title_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #0f172a;")
        filter_layout.addWidget(title_lbl)
        
        filter_layout.addStretch()
        
        date_lbl = QLabel("Select Date:")
        date_lbl.setStyleSheet("color: #475569;")
        filter_layout.addWidget(date_lbl)
        
        self.date_picker = QDateEdit(QDate.currentDate())
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setStyleSheet("padding: 6px; border: 1px solid #cbd5e1; border-radius: 6px; color: #0f172a;")
        filter_layout.addWidget(self.date_picker)
        
        self.btn_search = QPushButton("🔍 Search Logs")
        self.btn_search.setStyleSheet("background-color: #2563eb; color: white; padding: 6px 16px; border-radius: 6px; font-weight: bold;")
        filter_layout.addWidget(self.btn_search)
        
        layout.addWidget(filter_frame)
        
        # ─────────────── MAIN CONTENT VIEW ───────────────
        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)
        
        # ฝั่งซ้าย: ตารางรายการตรวจจับ
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Time", "Event Type", "Confidence", "Video File"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget { background-color: white; border: 1px solid #e2e8f0; border-radius: 8px; color: #0f172a; }
            QHeaderView::section { background-color: #f1f5f9; color: #475569; font-weight: bold; border: none; padding: 8px; }
        """)
        
        # ข้อมูลจำลองระบบ
        self._insert_mock_data("10:23:15", "Shoplifting Alert", "94.5%", "cam01_20260713_1023.mp4")
        self._insert_mock_data("11:45:02", "Suspicious Behavior", "88.2%", "cam02_20260713_1145.mp4")
        
        content_layout.addWidget(self.table, stretch=2)
        
        # ฝั่งขวา: จอจำลองสำหรับเล่นวิดีโอย้อนหลัง
        player_frame = QFrame()
        player_frame.setStyleSheet("background-color: #0f172a; border-radius: 8px; min-width: 320px;")
        player_layout = QVBoxLayout(player_frame)
        
        self.video_lbl = QLabel("🎬 Select a log row\nto play back video clip")
        self.video_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_lbl.setStyleSheet("color: #94a3b8; font-weight: bold;")
        player_layout.addWidget(self.video_lbl)
        
        content_layout.addWidget(player_frame, stretch=1)
        layout.addLayout(content_layout, stretch=1)

    def _insert_mock_data(self, time, event, conf, file):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(time))
        self.table.setItem(row, 1, QTableWidgetItem(event))
        self.table.setItem(row, 2, QTableWidgetItem(conf))
        self.table.setItem(row, 3, QTableWidgetItem(file))