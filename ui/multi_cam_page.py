# ui/multi_cam_page.py
import cv2
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QComboBox, QGridLayout, QFrame, QSizePolicy)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QImage, QPixmap

class MultiCamPage(QWidget):
    def __init__(self, camera_worker):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #f8fafc;")
        
        self.camera_worker = camera_worker
        self.camera_screens = {} # เก็บ dictionary ของออบเจกต์จอภาพกล้อง
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # ส่วนควบคุมบาร์ด้านบน
        header_layout = QHBoxLayout()
        header_lbl = QLabel("MULTI-CAMERA MONITORING")
        header_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header_lbl.setStyleSheet("color: #0f172a;")
        header_layout.addWidget(header_lbl)
        
        header_layout.addStretch()
        
        selector_lbl = QLabel("Select Grid:")
        selector_lbl.setFont(QFont("Segoe UI", 10))
        selector_lbl.setStyleSheet("color: #475569;")
        header_layout.addWidget(selector_lbl)
        
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["1 Camera", "2 Cameras", "4 Cameras", "6 Cameras"])
        self.layout_combo.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 6px 12px;
                color: #0f172a;
                min-width: 120px;
            }
        """)
        self.layout_combo.currentIndexChanged.connect(self._rebuild_camera_grid)
        header_layout.addWidget(self.layout_combo)
        layout.addLayout(header_layout)
        
        # กรอบตารางแสดงผลกล้อง
        self.grid_frame = QFrame()
        self.grid_frame.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;")
        self.grid_layout = QGridLayout(self.grid_frame)
        self.grid_layout.setSpacing(12)
        self.grid_layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(self.grid_frame, stretch=1)
        
        # เริ่มต้นสร้าง Grid ตัวแรก
        self._rebuild_camera_grid(0)
        
        # เชื่อมต่อสัญญาณภาพสดเข้ากับระบบอัปเดตช่องสัญญาณกล้องหลักแบบถาวร
        self.camera_worker.frame_received.connect(self._update_shared_frame)

    def _rebuild_camera_grid(self, index):
        # เคลียร์ป้ายเก่าออกจาก Grid ให้หมดก่อนจัดโครงสร้างใหม่
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
        
        self.camera_screens.clear()
        
        # 🟢 แปลงค่า Index คอมโบ้เป็นจำนวนกล้องจริงป้องกัน NameError
        num_cams = 1 if index == 0 else (2 if index == 1 else (4 if index == 2 else 6))
        cols = 1 if num_cams == 1 else (2 if num_cams <= 4 else 3)
        
        for i in range(num_cams):
            row = i // cols
            col = i % cols
            
            cam_box = QFrame()
            cam_box.setStyleSheet("background-color: #0f172a; border-radius: 6px;")
            box_lay = QVBoxLayout(cam_box)
            box_lay.setContentsMargins(0, 0, 0, 0)
            
            lbl_scr = QLabel()
            lbl_scr.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_scr.setScaledContents(False)
            lbl_scr.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
            
            if i == 0:
                lbl_scr.setText("Connecting Main Feed...")
                lbl_scr.setStyleSheet("color: #64748b;")
            else:
                lbl_scr.setText(f"📹 Camera {i+1}\n[STANDBY / SIMULATED FEED]")
                lbl_scr.setStyleSheet("color: #475569; font-size: 11px;")
                
            box_lay.addWidget(lbl_scr)
            self.grid_layout.addWidget(cam_box, row, col)
            self.camera_screens[i] = lbl_scr

    def _update_shared_frame(self, frame):
        # อัปเดตเฉพาะกล้องตำแหน่งที่ 0 (กล้องหลัก) หากแสดงผลอยู่ในตารางปัจจุบัน
        if 0 not in self.camera_screens or frame is None:
            return
            
        lbl_screen = self.camera_screens[0]
        if lbl_screen.width() <= 0 or lbl_screen.height() <= 0:
            return
            
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        qt_img = QImage(rgb_frame.data, w, h, ch * w, QImage.Format.Format_RGB888)
        
        lbl_screen.setPixmap(QPixmap.fromImage(qt_img).scaled(
            lbl_screen.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation
        ))