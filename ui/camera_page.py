# ui/camera_page.py
from PySide6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QLabel, QFrame, QSizePolicy
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
        
        # 🟢 บังคับให้หด/ขยายตามกรอบ QGridLayout เท่านั้น ไม่ดันขนาดออกไปข้างนอกเอง
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
            # รักษาสัดส่วนสตรีมมิ่งกล้อง ไม่ให้ภาพยืดแบน
            scaled = self.raw_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            super().setPixmap(scaled)


class CameraPage(QWidget):
    def __init__(self):
        super().__init__()
        self.state = AppState()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("📹 LIVE MULTI-CAMERA STREAM")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #e4e4e4; padding-bottom: 10px;")
        layout.addWidget(title)
        
        # Grid Layout สำหรับวางจอภาพกล้อง 4 ตัว
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(15)
        
        self.camera_views = {}
        # จำลองช่องใส่กล้อง 4 แชนเนล (Camera_0 ถึง Camera_3)
        for i in range(4):
            frame = QFrame()
            frame.setStyleSheet("background-color: #0f172a; border: 1px solid #1f4068; border-radius: 6px;")
            frame_layout = QVBoxLayout(frame)
            frame_layout.setContentsMargins(8, 8, 8, 8)
            
            # 🟢 เปลี่ยนมาใช้คลาสพิเศษป้องกันภาพเบี้ยวสเกล
            lbl_cam = AspectRatioPixmapLabel()
            lbl_cam.setStyleSheet("color: #64748b; font-size: 13px; border: none;")
            
            frame_layout.addWidget(lbl_cam)
            
            row = i // 2
            col = i % 2
            self.grid_layout.addWidget(frame, row, col)
            self.camera_views[f"Camera_{i}"] = lbl_cam
            
        layout.addLayout(self.grid_layout)
        
        # 🟢 สร้างตัวตั้งเวลาดึงเฟรมภาพมาอัปเดต (แต่ยังไม่เริ่มทำงานจนกว่าจะกดเข้าหน้านี้)
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_streams)

    # 🟢 [ฟังก์ชันดักจับเมื่อเปิดเข้าหน้านี้]: สั่งเปิดสัญญาณภาพ
    def showEvent(self, event):
        super().showEvent(event)
        self.timer.start(100) # ทำงานที่ 10 FPS

    # 🟢 [ฟังก์ชันดักจับเมื่อย้ายไปหน้าอื่น]: สั่งปิดสัญญาณภาพทันทีเพื่อประหยัด CPU/GPU
    def hideEvent(self, event):
        super().hideEvent(event)
        self.timer.stop()
        
        # ล้างภาพและข้อความค้างจอออกให้หมด
        for cam_key, lbl_view in self.camera_views.items():
            lbl_view.clear_camera("", "")

    def _update_streams(self):
        # ฟังก์ชันนี้จะประมวลผลสัญญาณเฉพาะตอนที่เรากำลังมองหน้าต่างนี้อยู่เท่านั้น
        for cam_key, lbl_view in self.camera_views.items():
            if cam_key in self.state.camera_pool:
                cam_data = self.state.camera_pool[cam_key]
                if cam_data.get("online", False) and cam_data.get("frame") is not None:
                    frame = cam_data["frame"]
                    
                    # แปลงช่องสี BGR (OpenCV) เป็น RGB (PySide)
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgb_frame.shape
                    bytes_per_line = ch * w
                    
                    qt_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                    pixmap = QPixmap.fromImage(qt_img)
                    
                    # อัปเดตส่งภาพลงจอ
                    lbl_view.set_camera_pixmap(pixmap)
                    continue
            
            # ถ้าไม่มีกล้องออนไลน์หรือหลุดการเชื่อมต่อ ให้เปลี่ยนสถานะเป็น Disconnected
            if lbl_view.raw_pixmap is not None or not lbl_view.text():
                cam_id = cam_key.split('_')[1]
                lbl_view.clear_camera(
                    f"Camera CH #{cam_id}\n[ Disconnected ]", 
                    "color: #64748b; font-size: 13px; border: none; qproperty-alignment: AlignCenter;"
                )