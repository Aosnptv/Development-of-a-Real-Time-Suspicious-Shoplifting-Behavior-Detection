# ui/multi_cam_page.py
import datetime
import cv2
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QComboBox, QGridLayout, QFrame, 
                               QGroupBox, QFormLayout, QSlider, QLineEdit,
                               QPushButton, QMessageBox)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QImage, QPixmap

class MultiCamPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f8fafc;")
        
        self.camera_screens = []
        self.caps = {} 
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # ─────────────── TOP BAR (CONTROL PANEL) ───────────────
        top_bar = QFrame()
        top_bar.setStyleSheet("background-color: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; padding: 12px;")
        top_layout = QHBoxLayout(top_bar)
        
        self.lbl_date = QLabel(f"Date: {datetime.date.today().strftime('%d/%m/%Y')}")
        self.lbl_date.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.lbl_date.setStyleSheet("color: #64748b;")
        
        self.lbl_sys = QLabel("System Status: Multi-Cam Matrix Mode")
        self.lbl_sys.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.lbl_sys.setStyleSheet("color: #2563eb;")
        
        cam_selector_layout = QHBoxLayout()
        lbl_select = QLabel("Select Channels Layout:")
        lbl_select.setStyleSheet("color: #334155; font-weight: bold; font-size: 12px;")
        
        self.combo_cams = QComboBox()
        self.combo_cams.addItems([f"{i} Channel" for i in range(1, 11)])
        self.combo_cams.setStyleSheet("""
            QComboBox { 
                background-color: #f1f5f9; color: #0f172a; padding: 6px 12px; 
                border-radius: 6px; border: 1px solid #cbd5e1; font-weight: bold;
            }
        """)
        self.combo_cams.currentIndexChanged.connect(self._rebuild_camera_grid)
        
        cam_selector_layout.addWidget(lbl_select)
        cam_selector_layout.addWidget(self.combo_cams)
        
        top_layout.addWidget(self.lbl_date)
        top_layout.addStretch()
        top_layout.addWidget(self.lbl_sys)
        top_layout.addSpacing(20)
        top_layout.addLayout(cam_selector_layout)
        layout.addWidget(top_bar)

        # ─────────────── PARAMETERS CONFIGURATION ───────────────
        group_ai = QGroupBox("AI Detection Parameters (Disabled)")
        group_ai.setStyleSheet("""
            QGroupBox { 
                color: #94a3b8; font-weight: bold; font-size: 13px;
                border: 1px solid #e2e8f0; border-radius: 8px; 
                margin-top: 10px; padding: 16px; background-color: #ffffff;
            }
        """)
        form_ai = QFormLayout(group_ai)
        form_ai.setVerticalSpacing(12)
        
        self.slider_thresh = QSlider(Qt.Orientation.Horizontal)
        self.slider_thresh.setEnabled(False)
        lbl_t = QLabel("Confidence Threshold:")
        lbl_t.setStyleSheet("color: #94a3b8; font-weight: bold;")
        form_ai.addRow(lbl_t, self.slider_thresh)
        layout.addWidget(group_ai)

        btn_save = QPushButton("Save System Settings")
        btn_save.setStyleSheet("background-color: #10b981; color: white; font-weight: bold; padding: 12px; border-radius: 6px; border: none;")
        layout.addWidget(btn_save)
        
        # ─────────────── CAMERA GRID AREA ───────────────
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(12)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.grid_container, stretch=1)
        
        self._rebuild_camera_grid(0)
        
        self.stream_timer = QTimer()
        self.stream_timer.timeout.connect(self._render_live_hardware_cameras)
        self.stream_timer.start(40) 

    def _rebuild_camera_grid(self, index):
        # เคลียร์กล้องเก่าออกก่อนเปิดใหม่เพื่อไม่ให้ทับซ้อนกัน
        for cap in self.caps.values():
            if cap and cap.isOpened():
                cap.release()
        self.caps.clear()
        self.camera_screens.clear()
        
        for i in reversed(range(self.grid_layout.count())): 
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
            
        num_cams = index + 1
        cols = 1 if num_cams == 1 else (2 if num_cams <= 4 else (3 if num_cams <= 6 else 4))
            
        for i in range(num_cams):
            row = i // cols
            col = i % cols
            
            cam_box = QFrame()
            cam_box.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;")
            box_layout = QVBoxLayout(cam_box)
            box_layout.setContentsMargins(8, 8, 8, 8)
            
            lbl_title = QLabel(f"CHANNEL {i+1:02d}")
            lbl_title.setStyleSheet("color: #0f172a; font-size: 11px; font-weight: bold;")
            
            lbl_screen = QLabel()
            lbl_screen.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_screen.setStyleSheet("background-color: #0f172a; border-radius: 6px;")
            
            box_layout.addWidget(lbl_title)
            box_layout.addWidget(lbl_screen, stretch=1)
            
            self.grid_layout.addWidget(cam_box, row, col)
            self.camera_screens.append(lbl_screen)

            # 🟢 เปิดใช้งานผ่าน cv2.CAP_DSHOW เพื่อแก้ปัญหาภาพซูมผิดปกติบน Windows
            # หากกล้อง 0 ถูก Dashboard ใช้ไปแล้ว ตัวนี้จะขยับไปเปิดกล้องถัดไป (เช่น กล้อง 1) อัตโนมัติ หรือถ้าไม่มีจะแสดง Error สวย ๆ ครับ
            cam_index = i if i > 0 else 0 
            cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
            if cap.isOpened():
                # ตั้งความละเอียดมาตรฐานเพื่อไม่ให้เลนส์เพี้ยน/ซูม
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.caps[i] = cap
            else:
                # ถ้ากล้อง 0 โดนแย่ง ลองเปิดกล้องสำรองหรือข้ามไป
                cap_alt = cv2.VideoCapture(cam_index + 1, cv2.CAP_DSHOW)
                if cap_alt.isOpened():
                    self.caps[i] = cap_alt

    def _render_live_hardware_cameras(self):
        for idx, lbl_screen in enumerate(self.camera_screens):
            if lbl_screen.width() <= 0 or lbl_screen.height() <= 0:
                continue
                
            cap = self.caps.get(idx)
            if cap and cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgb_frame.shape
                    bytes_per_line = ch * w
                    
                    qt_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                    lbl_screen.setPixmap(QPixmap.fromImage(qt_img).scaled(
                        lbl_screen.size(), 
                        Qt.AspectRatioMode.KeepAspectRatio, 
                        Qt.TransformationMode.SmoothTransformation
                    ))
                else:
                    lbl_screen.setText("⚠️ [OCCUPIED / NO SIGNAL]\nCamera is being used by Dashboard")
                    lbl_screen.setStyleSheet("color: #f97316; font-size: 11px; font-weight: bold; background-color: #0f172a; qproperty-alignment: AlignCenter;")
            else:
                lbl_screen.setText("❌ CAMERA NOT AVAILABLE\n(In Use by Another Page)")
                lbl_screen.setStyleSheet("color: #ef4444; font-size: 11px; font-weight: bold; background-color: #0f172a; qproperty-alignment: AlignCenter;")

    def closeEvent(self, event):
        for cap in self.caps.values():
            if cap and cap.isOpened():
                cap.release()
        event.accept()
    
    def _rebuild_camera_grid(self, index):
        # เคลียร์พอร์ตเก่าออกให้หมดก่อน
        for cap in self.caps.values():
            if cap and cap.isOpened():
                cap.release()
        self.caps.clear()
        self.camera_screens.clear()
        
        # ... (โค้ดจัดการ Layout เหมือนเดิม) ...
            
        for i in range(num_cams):
            # ... (สร้างเฟรมและป้ายชื่อเหมือนเดิม) ...
            
            cam_index = i if i > 0 else 0 
            cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
            if cap.isOpened():
                # 🟢 ล็อคขนาดและปิดระบบออโต้ซูมระดับฮาร์ดแวร์เพื่อหยุดกล้องขยายตัวเอง
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
                self.caps[i] = cap

    def _render_live_hardware_cameras(self):
        for idx, lbl_screen in enumerate(self.camera_screens):
            if lbl_screen.width() <= 0 or lbl_screen.height() <= 0:
                continue
                
            cap = self.caps.get(idx)
            if cap and cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgb_frame.shape
                    bytes_per_line = ch * w
                    
                    qt_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                    base_pixmap = QPixmap.fromImage(qt_img)
                    
                    # 🟢 บังคับควบคุมขนาดการแสดงผลไม่ให้ฝั่งหน้าต่างบีบอัดภาพจนเกิดการซูมเลนส์
                    lbl_screen.setPixmap(base_pixmap.scaled(
                        lbl_screen.size(), 
                        Qt.AspectRatioMode.KeepAspectRatio, 
                        Qt.TransformationMode.FastTransformation
                    ))
    def _rebuild_camera_grid(self, index):
        # เคลียร์พอร์ตเก่าออกให้หมดก่อน
        for cap in self.caps.values():
            if cap and cap.isOpened():
                cap.release()
        self.caps.clear()
        self.camera_screens.clear()
        
        for i in reversed(range(self.grid_layout.count())): 
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
            
        # 🟢 เติมบรรทัดนี้กลับเข้าไปครับ (ตัวแปรที่หายไป)
        num_cams = index + 1
        
        # คำนวณจำนวนคอลัมน์ของ Grid กล้อง
        cols = 1 if num_cams == 1 else (2 if num_cams <= 4 else (3 if num_cams <= 6 else 4))
            
        # ลูปสร้างกล้องจะกลับมาทำงานได้ปกติแล้วครับ
        for i in range(num_cams):
            row = i // cols
            col = i % cols
            
            # ... (โค้ดสร้าง QFrame และเปิด cv2.VideoCapture ด้านล่างปล่อยไว้เหมือนเดิมได้เลย) ...