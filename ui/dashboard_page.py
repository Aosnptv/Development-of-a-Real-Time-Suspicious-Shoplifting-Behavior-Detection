# ui/dashboard_page.py
import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QGridLayout, QFrame, QSizePolicy, QComboBox)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QImage, QPixmap
import cv2
from core.app_state import AppState

class AspectRatioPixmapLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.raw_pixmap = None  
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)

    def set_camera_pixmap(self, pixmap):
        self.raw_pixmap = pixmap
        self.update_scaled_pixmap()

    def clear_camera(self, text, stylesheet=None):
        self.raw_pixmap = None
        self.setPixmap(QPixmap())
        self.setText(text)
        if stylesheet:
            self.setStyleSheet(stylesheet)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.raw_pixmap and not self.raw_pixmap.isNull():
            self.update_scaled_pixmap()

    def update_scaled_pixmap(self):
        if self.raw_pixmap:
            scaled = self.raw_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            super().setPixmap(scaled)


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f8fafc;")
        
        self.state = AppState()
        self.monitor_slots = []
        
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
        lbl_monitor = QLabel("Live System Monitor (Select 2 of 10 Channels)")
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
            box_lay.setContentsMargins(8, 8, 8, 8)
            box_lay.setSpacing(8)
            
            combo_cam = QComboBox()
            combo_cam.setStyleSheet("""
                QComboBox {
                    background-color: #1e293b; color: #f8fafc;
                    border: 1px solid #475569; border-radius: 4px;
                    padding: 4px 8px; font-weight: bold;
                }
                QComboBox QAbstractItemView {
                    background-color: #1e293b; color: #f8fafc;
                    selection-background-color: #2563eb;
                }
            """)
            
            for ch in range(10):
                combo_cam.addItem(f"🎥 Camera CH #{ch}", f"Camera_{ch}")
            
            combo_cam.setCurrentIndex(i)
            box_lay.addWidget(combo_cam)
            
            lbl_scr = AspectRatioPixmapLabel()
            lbl_scr.setStyleSheet("color: #64748b; font-size: 13px;")
            box_lay.addWidget(lbl_scr)
            
            self.monitor_slots.append({
                "combo": combo_cam,
                "label": lbl_scr
            })
            
            self.grid_layout.addWidget(cam_box, 0, i)
            
        layout.addWidget(grid_frame, stretch=1)
        
        # 🟢 สร้าง Timer ไว้ แต่ยังไม่สั่ง .start() จนกว่าหน้า UI จะถูกเปิดขึ้นมาจริงๆ
        self.stream_timer = QTimer()
        self.stream_timer.timeout.connect(self._render_selected_streams)

    # 🟢 [จุดเช็คสำคัญที่ 1]: ถ้าผู้ใช้งานเปิดสลับมาที่หน้าแรก (Dashboard)
    def showEvent(self, event):
        super().showEvent(event)
        # สั่งให้ Timer เริ่มดึงข้อมูลกล้องทันที (ทำงานที่ 10 FPS)
        self.stream_timer.start(100)

    # 🟢 [จุดเช็คสำคัญที่ 2]: ถ้าสลับหนีไปหน้าอื่น (เช่น หน้ากล้องรวม หรือหน้าตั้งค่า)
    def hideEvent(self, event):
        super().hideEvent(event)
        # สั่งหยุด Timer ทันที เพื่อไม่ให้กินทรัพยากรเครื่องในเบื้องหลัง
        self.stream_timer.stop()
        
        # ล้างการจองหน่วยความจำภาพบนหน้าจอออกให้หมด
        for slot in self.monitor_slots:
            slot["label"].clear_camera("", "")

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

    def _render_selected_streams(self):
        # ฟังก์ชันนี้จะทำงานเฉพาะตอนที่หน้า Dashboard แปะอยู่บนจอเท่านั้น
        for slot in self.monitor_slots:
            combo = slot["combo"]
            lbl_screen = slot["label"]
            selected_cam_key = combo.currentData()
            
            if selected_cam_key in self.state.camera_pool:
                cam_data = self.state.camera_pool[selected_cam_key]
                
                if cam_data.get("online", False) and cam_data.get("frame") is not None:
                    frame = cam_data["frame"]
                    
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgb_frame.shape
                    bytes_per_line = ch * w
                    
                    qt_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                    base_pixmap = QPixmap.fromImage(qt_img)
                    
                    lbl_screen.set_camera_pixmap(base_pixmap)
                    continue
            
            if lbl_screen.raw_pixmap is not None or not lbl_screen.text():
                cam_label_text = combo.currentText()
                lbl_screen.clear_camera(
                    f"{cam_label_text}\n[ Disconnected ]", 
                    "color: #64748b; font-size: 13px; qproperty-alignment: AlignCenter;"
                )