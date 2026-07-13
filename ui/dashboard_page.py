# ui/dashboard_page.py
import datetime
import cv2
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QGridLayout, QFrame)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QImage, QPixmap

class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f8fafc;")
        
        self.monitor_screens = []
        
        # 🟢 เปลี่ยนมาใช้ cv2.CAP_DSHOW ป้องกันอาการภาพติดซูมบน Windows OS
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # ─────────────── HEADER AREA ───────────────
        header = QLabel("DASHBOARD OVERVIEW")
        header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header.setStyleSheet("color: #0f172a;")
        layout.addWidget(header)
        
        # ─────────────── STATS CARDS ───────────────
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
            box_lay.addWidget(lbl_scr)
            
            self.grid_layout.addWidget(cam_box, 0, i)
            self.monitor_screens.append(lbl_scr)
            
        layout.addWidget(grid_frame, stretch=1)
        
        self.stream_timer = QTimer()
        self.stream_timer.timeout.connect(self._render_real_camera_streams)
        self.stream_timer.start(33)

    def _create_stat_card(self, title, val, color):
        card = QFrame()
        card.setStyleSheet(f"background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; border-left: 5px solid {color};")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 16, 16, 16)
        
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("color: #64748b; font-size: 12px; font-weight: bold;")
        v_lbl = QLabel(val)
        v_lbl.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        v_lbl.setStyleSheet(f"color: {color};")
        
        lay.addWidget(t_lbl)
        lay.addWidget(v_lbl)
        return card

    def _render_real_camera_streams(self):
        if not self.monitor_screens:
            return
            
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_frame.shape
                bytes_per_line = ch * w
                qt_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                
                for lbl_screen in self.monitor_screens:
                    if lbl_screen.width() <= 0 or lbl_screen.height() <= 0:
                        continue
                    lbl_screen.setPixmap(QPixmap.fromImage(qt_img).scaled(
                        lbl_screen.size(), 
                        Qt.AspectRatioMode.KeepAspectRatio, 
                        Qt.TransformationMode.SmoothTransformation
                    ))
            else:
                for lbl_screen in self.monitor_screens:
                    lbl_screen.setText("❌ NO SIGNAL (GRAB FAILED)")
                    lbl_screen.setStyleSheet("color: white; background-color: #0f172a;")
        else:
            for lbl_screen in self.monitor_screens:
                lbl_screen.setText("⚠️ CAMERA OCCUPIED BY MULTI-CAM PAGE")
                lbl_screen.setStyleSheet("color: #eab308; background-color: #0f172a;")

    def closeEvent(self, event):
        if self.cap.isOpened():
            self.cap.release()
        event.accept()
    
    # เพิ่มการกำหนดค่าวิดีโอตั้งแต่แรกใน __init__ ครั้งเดียว และล็อกความละเอียดคงที่
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f8fafc;")
        self.monitor_screens = []
        
        # 🟢 เปิดกล้องและล็อกค่าทันที ไม่สลับหรือตั้งค่าซ้ำใน Loop
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            # 🔴 ปิดฟังก์ชัน Auto Focus และ Auto Zoom ของ Windows ที่ทำให้เลนส์ขยายเอง
            self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0) 
            
        # ... (โค้ดสร้าง UI อื่น ๆ เหมือนเดิม) ...

    def _render_real_camera_streams(self):
        if not self.monitor_screens:
            return
            
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # แปลงสีปกติ
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_frame.shape
                bytes_per_line = ch * w
                qt_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                
                # 🟢 จุดสำคัญ: บังคับแปลงเป็น QPixmap ขนาดฟิกซ์ตามสัดส่วนกล้อง 4:3 ก่อน 
                # เพื่อป้องกันไม่ให้ระเบิดขนาดกล้องขยายตามขนาด Widget ที่กว้างขึ้นเรื่อย ๆ
                base_pixmap = QPixmap.fromImage(qt_img)
                
                for lbl_screen in self.monitor_screens:
                    if lbl_screen.width() <= 0 or lbl_screen.height() <= 0:
                        continue
                        
                    # ล็อกสัดส่วนการย่อ/ขยายปลายทางอย่างเคร่งครัด (KeepAspectRatio)
                    lbl_screen.setPixmap(base_pixmap.scaled(
                        lbl_screen.size(), 
                        Qt.AspectRatioMode.KeepAspectRatio, 
                        Qt.TransformationMode.FastTransformation # เปลี่ยนเป็น Fast เพื่อเคลียร์ Buffer ตกค้าง
                    ))
            else:
                for lbl_screen in self.monitor_screens:
                    lbl_screen.setText("❌ NO SIGNAL")
        else:
            for lbl_screen in self.monitor_screens:
                lbl_screen.setText("⚠️ CAMERA OCCUPIED")