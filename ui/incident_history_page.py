from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QColor
import os
from services.database_service import DatabaseService

class IncidentHistoryPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseService()
        self.all_incidents = [] # เก็บข้อมูลดิบจาก DB ไว้ค้นหา
        self.setup_ui()
        self.load_data_from_db()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # หัวข้อหน้าจอ
        lbl_title = QLabel("📋 หน้าค้นหาและตรวจสอบประวัติพฤติกรรมต้องสงสัย (Incident History)")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        main_layout.addWidget(lbl_title)

        # =============================================================
        # ส่วนที่ 1: แถบค้นหาและคัดกรองข้อมูล (Filters) ตามขอบเขตวิจัย
        # =============================================================
        filter_layout = QHBoxLayout()
        
        # ค้นหาด้วย Person ID
        self.txt_search_id = QLineEdit()
        self.txt_search_id.setPlaceholderText("🔎 ค้นหาด้วยรหัสบุคคล (Person ID)...")
        self.txt_search_id.textChanged.connect(self.filter_data)
        
        # ตัวเลือกกรองตามกล้อง
        self.cb_filter_camera = QComboBox()
        self.cb_filter_camera.addItems(["📷 แสดงทุกกล้อง", "Camera 1", "Camera 2"])
        self.cb_filter_camera.currentIndexChanged.connect(self.filter_data)

        # ตัวเลือกกรองตามสถานะ
        self.cb_filter_status = QComboBox()
        self.cb_filter_status.addItems(["🔔 ทุกสถานะ", "Unresolved", "Resolved"])
        self.cb_filter_status.currentIndexChanged.connect(self.filter_data)

        filter_layout.addWidget(self.txt_search_id, stretch=4)
        filter_layout.addWidget(self.cb_filter_camera, stretch=2)
        filter_layout.addWidget(self.cb_filter_status, stretch=2)
        main_layout.addLayout(filter_layout)

        # =============================================================
        # ส่วนที่ 2: แบ่งฝั่ง [ ซ้าย: ตารางข้อมูล ตาราง ] | [ ขวา: กรอบโชว์ภาพ Snapshot ]
        # =============================================================
        content_layout = QHBoxLayout()

        # ฝั่งซ้าย: ตารางประวัติเหตุการณ์
        self.table_incidents = QTableWidget()
        self.table_incidents.setColumnCount(6)
        self.table_incidents.setHorizontalHeaderLabels(["ID", "เวลาเกิดเหตุ", "กล้อง", "Person ID", "Suspicion Score", "สถานะ"])
        self.table_incidents.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_incidents.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_incidents.itemSelectionChanged.connect(self.on_row_selected) # เมื่อกดเลือกแถว ให้ไปโชว์ภาพ
        content_layout.addWidget(self.table_incidents, stretch=7)

        # ฝั่งขวา: กรอบแสดงภาพหลักฐาน (Snapshot Viewer)
        self.right_panel = QFrame()
        self.right_panel.setFixedWidth(360)
        self.right_panel.setStyleSheet("background-color: #1e293b; border-radius: 8px;")
        right_layout = QVBoxLayout(self.right_panel)
        
        lbl_panel_title = QLabel("🖼️ ภาพหลักฐานเหตุการณ์ (Snapshot)")
        lbl_panel_title.setStyleSheet("font-weight: bold; color: #94a3b8; font-size: 14px;")
        lbl_panel_title.setAlignment(Qt.AlignCenter)
        
        self.lbl_snapshot_view = QLabel("💡 คลิกเลือกรายการในตาราง\nเพื่อดูภาพหลักฐาน")
        self.lbl_snapshot_view.setAlignment(Qt.AlignCenter)
        self.lbl_snapshot_view.setWordWrap(True)
        self.lbl_snapshot_view.setStyleSheet("color: #64748b; font-size: 14px;")
        
        right_layout.addWidget(lbl_panel_title)
        right_layout.addWidget(self.lbl_snapshot_view, stretch=1)
        
        content_layout.addWidget(self.right_panel)
        main_layout.addLayout(content_layout)

    def load_data_from_db(self):
        """ดึงข้อมูลดิบจาก SQLite มาเก็บไว้ใน Memory"""
        # อ้างอิงโครงสร้าง DB ตามเล่มวิจัย: (id, datetime, camera, person_id, score, status, snapshot)
        self.all_incidents = self.db.get_all_incidents()
        self.filter_data() # เอาข้อมูลไปแจกจ่ายลงตาราง

    def filter_data(self):
        """ฟังก์ชันค้นหาและคัดกรองข้อมูล Real-time"""
        search_text = self.txt_search_id.text().strip().lower()
        selected_cam_idx = self.cb_filter_camera.currentIndex() # 0=ทั้งหมด, 1=Cam1, 2=Cam2
        selected_status_text = self.cb_filter_status.currentText()

        # คัดกรองข้อมูลตามเงื่อนไข
        filtered_list = []
        for item in self.all_incidents:
            # โครงสร้างในฐานข้อมูล: inc_id, datetime, camera_id, person_id, score, status, snapshot_path
            inc_id, dt, cam_id, pid, score, status, img_path = item
            
            # 1. กรองจากรหัสบุคคล (Person ID)
            if search_text and search_text not in f"person id: {pid}".lower() and search_text not in str(pid):
                continue
            
            # 2. กรองจากตัวเลือกกล้อง
            if selected_cam_idx == 1 and cam_id != 0: continue
            if selected_cam_idx == 2 and cam_id != 1: continue

            # 3. กรองจากตัวเลือกสถานะ
            if selected_status_text != "🔔 ทุกสถานะ" and status != selected_status_text:
                continue

            filtered_list.append(item)

        # วาดข้อมูลลงตารางจริง
        self.table_incidents.setRowCount(0)
        self.table_incidents.setRowCount(len(filtered_list))
        
        for row_idx, item in enumerate(filtered_list):
            inc_id, dt, cam_id, pid, score, status, img_path = item
            cam_name = f"Camera {cam_id + 1}"
            
            # ใส่ไอเทมลงช่องตาราง และแอบเก็บ File Path รูปภาพเอาไว้ในช่อง ID
            id_item = QTableWidgetItem(str(inc_id))
            id_item.setData(Qt.UserRole, img_path) # ซ่อน Path รูปไว้ที่แถวนี้
            
            self.table_incidents.setItem(row_idx, 0, id_item)
            self.table_incidents.setItem(row_idx, 1, QTableWidgetItem(str(dt)))
            self.table_incidents.setItem(row_idx, 2, QTableWidgetItem(cam_name))
            self.table_incidents.setItem(row_idx, 3, QTableWidgetItem(f"ID: {pid}"))
            self.table_incidents.setItem(row_idx, 4, QTableWidgetItem(f"{score} pts"))
            
            status_item = QTableWidgetItem(status)
            if status == "Unresolved":
                status_item.setForeground(QColor("#ef4444")) # ไฮไลต์สีแดงกรณีขโมยยังไม่เคลียร์
            self.table_incidents.setItem(row_idx, 5, status_item)

    def on_row_selected(self):
        """เมื่อกดเลือกแถวในตาราง ให้ดึงรูป Snapshot มาแสดงทันที"""
        selected_rows = self.table_incidents.selectionModel().selectedRows()
        if not selected_rows:
            return
            
        row_idx = selected_rows[0].row()
        id_item = self.table_incidents.item(row_idx, 0)
        img_path = id_item.data(Qt.UserRole) # ดึง Path รูปที่ซ่อนไว้ขึ้นมา

        if img_path and os.path.exists(img_path):
            pixmap = QPixmap(img_path)
            scaled = pixmap.scaled(340, 260, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.lbl_snapshot_view.setPixmap(scaled)
        else:
            self.lbl_snapshot_view.clear()
            self.lbl_snapshot_view.setText("❌ ไม่พบไฟล์ภาพหลักฐาน\nหรือไฟล์ถูกลบไปแล้ว")