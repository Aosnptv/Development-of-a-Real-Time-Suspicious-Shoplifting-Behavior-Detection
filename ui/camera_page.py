from PySide6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QImage, QPixmap
from core.app_state import AppState

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
            
            lbl_cam = QLabel(f"Camera CH #{i}\n[ Disconnected ]")
            lbl_cam.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_cam.setStyleSheet("color: #64748b; font-size: 13px; border: none;")
            
            frame_layout.addWidget(lbl_cam)
            
            row = i // 2
            col = i % 2
            self.grid_layout.addWidget(frame, row, col)
            self.camera_views[f"Camera_{i}"] = lbl_cam
            
        layout.addLayout(self.grid_layout)
        
        # ตัวตั้งเวลาดึงเฟรมภาพมาอัปเดต (10 FPS)
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_streams)
        self.timer.start(100)
        
    def _update_streams(self):
        for cam_key, lbl_view in self.camera_views.items():
            if cam_key in self.state.camera_pool:
                cam_data = self.state.camera_pool[cam_key]
                if cam_data.get("online", False) and cam_data.get("frame") is not None:
                    frame = cam_data["frame"]
                    h, w, ch = frame.shape
                    qt_img = QImage(frame.data, w, h, ch * w, QImage.Format.Format_BGR888)
                    pixmap = QPixmap.fromImage(qt_img)
                    lbl_view.setPixmap(pixmap.scaled(lbl_view.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                    continue
            
            # ถ้าไม่มีกล้องออนไลน์ให้เคลียร์สกรีนเป็นข้อความเดิม
            if not lbl_view.text():
                lbl_view.setPixmap(QPixmap())
                lbl_view.setText(f"{cam_key}\n[ Disconnected ]")