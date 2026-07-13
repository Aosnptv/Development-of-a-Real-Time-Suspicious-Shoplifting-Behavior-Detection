# ui/dashboard_page.py
import cv2
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QGridLayout, QFrame, QSizePolicy)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QImage, QPixmap

class DashboardPage(QWidget):
    def __init__(self, camera_worker): 
        super().__init__()
        # 🟢 เปิดสวิตช์บังคับวาดพื้นหลังตาม Stylesheet แก้ปัญหาหน้าจอมืดสนิท
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #f8fafc;")
        
        # 🟢 ลำดับที่ 1: สร้าง Layout หลักของหน้าต่างก่อนชิ้นส่วนอื่น
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        self.monitor_screens = []
        
        # เชื่อมต่อสัญญาณรับภาพจากแกนกล้องส่วนกลาง
        self.camera_worker = camera_worker
        self.camera_worker.frame_received.connect(self._update_ui_frame)
        
        # ─────────────── HEADER AREA ───────────────
        header = QLabel("DASHBOARD OVERVIEW")
        header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header.setStyleSheet("color: #0f172a;")
        layout.addWidget(header)
        
        # ─────────────── STATS CARDS AREA ───────────────
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)
        
        self.card_total = self._create_stat_card("Total Detections", "0", "#2563eb")
        self.card_suspicious = self._create_stat_card("Suspicious Behavior", "0", "#ea580c")
        self.card_shoplift = self._create_stat_card("Shoplifting Alerts", "0", "#dc2626")
        
        stats_layout.addWidget(self.card_total)
        stats_layout.addWidget(self.card_suspicious)
        stats_layout.addWidget(self.card_shoplift)
        layout.addLayout(stats_layout)
        
        # ─────────────── LIVE MONITORING GRID ───────────────
        lbl_monitor = QLabel("Live System Monitor (Main Feed)")
        lbl_monitor.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl_monitor.setStyleSheet("color: #334155; margin-top: 10px;")
        layout.addWidget(lbl_monitor)
        
        grid_frame = QFrame()
        grid_frame.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;")
        self.grid_layout = QGridLayout(grid_frame)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setContentsMargins(16, 16, 16, 16)
        
        for i in range(2):
            cam_box = QFrame()
            cam_box.setStyleSheet("background-color: #0f172a; border-radius: 6px;")
            box_lay = QVBoxLayout(cam_box)
            box_lay.setContentsMargins(0, 0, 0, 0)
            
            lbl_scr = QLabel()
            lbl_scr.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_scr.setScaledContents(False)
            # 🟢 ล็อคขนาด Ignored ป้องกัน Size Hint วนลูปดันหน้าต่างให้ขยายใหญ่เอง
            lbl_scr.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
            
            box_lay.addWidget(lbl_scr)
            self.grid_layout.addWidget(cam_box, 0, i)
            self.monitor_screens.append(lbl_scr)
            
        layout.addWidget(grid_frame, stretch=1)

    def _create_stat_card(self, title, value, color_hex):
        card = QFrame()
        card.setStyleSheet(f"""
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            border-left: 5px solid {color_hex};
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        
        lbl_title = QLabel(title)
        lbl_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_title.setStyleSheet("color: #64748b;")
        
        lbl_val = QLabel(value)
        lbl_val.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        lbl_val.setStyleSheet("color: #0f172a; margin-top: 4px;")
        
        card_layout.addWidget(lbl_title)
        card_layout.addWidget(lbl_val)
        return card

    def _update_ui_frame(self, frame):
        if not self.monitor_screens or frame is None:
            return
            
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        base_pixmap = QPixmap.fromImage(qt_img)
        
        for lbl_screen in self.monitor_screens:
            if lbl_screen.width() <= 0 or lbl_screen.height() <= 0:
                continue
            lbl_screen.setPixmap(base_pixmap.scaled(
                lbl_screen.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.FastTransformation
            ))  