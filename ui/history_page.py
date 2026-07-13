from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QHBoxLayout, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import sqlite3 
import os

class HistoryPage(QWidget):
    def __init__(self):
        super().__init__()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        header = QHBoxLayout()
        title = QLabel("📜 INCIDENT DETECTION HISTORY")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #e4e4e4;")
        
        btn_refresh = QPushButton("🔄 Refresh Log")
        btn_refresh.setStyleSheet("background-color: #1f4068; color: white; padding: 6px 15px; border-radius: 4px; border: none;")
        btn_refresh.clicked.connect(self.load_data_from_db)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(btn_refresh)
        layout.addLayout(header)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Camera ID", "Detected Event", "Confidence", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        self.table.setStyleSheet("""
            QTableWidget { background-color: #162447; color: #e4e4e4; gridline-color: #1f4068; border: 1px solid #1f4068; border-radius: 6px; }
            QHeaderView::section { background-color: #1f4068; color: #00adb5; font-weight: bold; padding: 6px; border: 1px solid #162447; }
        """)
        
        layout.addWidget(self.table)
        self.load_data_from_db()
        
    def load_data_from_db(self):
        """ดึงข้อมูลจากไฟล์ SQLite โดยตรงแบบปลอดภัย"""
        db_path = "incidents.db" 
        
        # เคลียร์ข้อมูลเก่าในตารางออกก่อนทุกครั้งที่โหลดใหม่ เพื่อป้องกันข้อมูลซ้ำซ้อน
        self.table.clearContents()
        self.table.setRowCount(0)
        
        if not os.path.exists(db_path):
            self._load_mock_data()
            return
            
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT timestamp, camera_id, event_label, confidence, image_path FROM incidents ORDER BY timestamp DESC LIMIT 100")
            rows = cursor.fetchall()
            
            self.table.setRowCount(len(rows))
            for row_idx, row_data in enumerate(rows):
                timestamp, cam_id, event_label, conf, img_path = row_data
                display_data = [timestamp, cam_id, event_label, f"{conf * 100:.1f}%" if isinstance(conf, float) and conf <= 1.0 else f"{conf}%"]
                
                for col_idx, text in enumerate(display_data):
                    item = QTableWidgetItem(str(text))
                    item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                    self.table.setItem(row_idx, col_idx, item)
                    
                btn_view = QPushButton("View Snapshot")
                btn_view.setStyleSheet("background-color: #00adb5; color: white; border-radius: 3px; max-width: 100px;")
                
                # 🟢 แก้ไขตรงนี้: ใช้ default parameter (path=img_path) เพื่อบังคับให้ขังค่าคงที่ของแต่ละรอบไว้ ไม่ให้เกิด Late Binding
                btn_view.clicked.connect(lambda checked=False, path=img_path: self._show_snapshot(path))
                self.table.setCellWidget(row_idx, 4, btn_view)
                
            conn.close()
        except Exception as e:
            print(f"Database Fallback Error: {e}")
            self._load_mock_data()

    def _load_mock_data(self):
        """โหลดข้อมูลจำลองในกรณีที่ยังเชื่อมต่อฐานข้อมูลหลักไม่ได้"""
        mock_incidents = [
            ("2026-07-13 14:23:01", "Camera_0", "Shoplifting (Pocketing)", "89.4%", "mock_path_0.jpg"),
            ("2026-07-13 15:05:42", "Camera_1", "Suspicious Loitering", "76.2%", "mock_path_1.jpg"),
        ]
        self.table.setRowCount(len(mock_incidents))
        for row_idx, data in enumerate(mock_incidents):
            for col_idx, text in enumerate(data[:-1]): # ไม่เอาพาทรูปไปใส่ในช่อง Text ปกติ
                item = QTableWidgetItem(text)
                item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                self.table.setItem(row_idx, col_idx, item)
                
            btn = QPushButton("View Snapshot")
            btn.setStyleSheet("background-color: #00adb5; color: white; border-radius: 3px; max-width: 100px;")
            
            # 🟢 แก้ไขตรงนี้ด้วยเช่นกันสำหรับข้อมูลจำลอง
            btn.clicked.connect(lambda checked=False, path=data[4]: self._show_snapshot(path))
            self.table.setCellWidget(row_idx, 4, btn)
                    
    def _show_snapshot(self, img_path):
        msg = QMessageBox(self)
        msg.setWindowTitle("Incident Snapshot Location")
        msg.setText(f"Target Image Path:\n{img_path}")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()