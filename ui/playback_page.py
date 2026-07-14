from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QFrame
from PySide6.QtCore import Qt

class PlaybackPage(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        self.title = QLabel("⏪ Playback & Event History")
        self.title.setStyleSheet("font-size: 20px; font-weight: bold;")
        main_layout.addWidget(self.title)
        
        # ─────────────── แบ่งหน้าจอ ซ้าย-ขวา ───────────────
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # ฝั่งซ้าย: ตารางเหตุการณ์
        self.table = QTableWidget(5, 4)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Camera", "Event Type", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        mock_data = [
            ("2026-07-14 23:15:02", "Camera 0", "Suspicious Behavior", "Alert Sent"),
            ("2026-07-14 22:40:11", "Camera 1", "Normal", "Logged"),
            ("2026-07-14 21:05:54", "Camera 0", "Shoplifting Detected", "Telegram Notified"),
            ("2026-07-14 19:30:22", "Camera 1", "Suspicious Behavior", "Reviewed"),
            ("2026-07-14 18:12:00", "Camera 0", "Normal", "Logged")
        ]
        
        for row, data in enumerate(mock_data):
            for col, text in enumerate(data):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)
                
        content_layout.addWidget(self.table, stretch=2)
        
        # 🟢 ฝั่งขวา: เพิ่มช่องสำหรับดูภาพล่าสุดที่แคป (Snapshot Panel) ตามคำขอ
        self.snapshot_panel = QFrame()
        snapshot_lay = QVBoxLayout(self.snapshot_panel)
        snapshot_lay.setContentsMargins(15, 15, 15, 15)
        
        self.lbl_snap_title = QLabel("📸 Latest Event Snapshot")
        snapshot_lay.addWidget(self.lbl_snap_title)
        
        self.lbl_snapshot = QLabel("No Event Selected\n\n(Select a row from history to view)")
        self.lbl_snapshot.setAlignment(Qt.AlignCenter)
        self.lbl_snapshot.setMinimumSize(320, 240)
        snapshot_lay.addWidget(self.lbl_snapshot, stretch=1)
        
        content_layout.addWidget(self.snapshot_panel, stretch=1)
        main_layout.addLayout(content_layout)

    def set_theme(self, is_dark_mode):
        # เปลี่ยนสีตัวอักษรและพื้นหลังของทุก Widget ตามธีม
        self.title.setStyleSheet(f"color: {'white' if is_dark_mode else 'black'}; font-size: 20px; font-weight: bold;")
        
        bg = "#1e293b" if is_dark_mode else "#ffffff"
        fg = "white" if is_dark_mode else "black"
        grid = "#334155" if is_dark_mode else "#cbd5e1"
        bg_lbl = "#0f172a" if is_dark_mode else "#e2e8f0"
        
        # สไตล์ตาราง
        self.table.setStyleSheet(f"""
            QTableWidget {{ background-color: {bg}; color: {fg}; gridline-color: {grid}; border: 1px solid {grid}; }}
            QHeaderView::section {{ background-color: {'#0f172a' if is_dark_mode else '#e2e8f0'}; color: {fg}; padding: 6px; border: 1px solid {grid}; font-weight: bold; }}
            QTableWidget::item {{ color: {fg}; }}
        """)
        
        # สไตล์กล่อง Snapshot ด้านขวา
        self.snapshot_panel.setStyleSheet(f"background-color: {bg}; border: 1px solid {grid}; border-radius: 8px;")
        self.lbl_snap_title.setStyleSheet(f"color: {'#38bdf8' if is_dark_mode else '#2563eb'}; font-weight: bold; font-size: 14px; border: none; background: transparent;")
        self.lbl_snapshot.setStyleSheet(f"background-color: {bg_lbl}; color: {'#94a3b8' if is_dark_mode else '#475569'}; border: 1px dashed {grid}; border-radius: 6px; font-weight: bold; font-size: 12px;")