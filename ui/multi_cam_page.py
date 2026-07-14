from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap

class MultiCamPage(QWidget):
    def __init__(self, camera_worker):
        super().__init__()
        self.camera_worker = camera_worker
        self.zoom_level = 2 
        self.video_labels = {}
        self.cam_statuses = {} # 🟢 ตัวจำสถานะเพื่อบล็อกการดีดของ CPU
        self.current_theme_dark = True
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        
        top_layout = QHBoxLayout()
        self.title = QLabel("📹 Multi-Cam Grid View")
        self.title.setStyleSheet("font-size: 20px; font-weight: bold;")
        top_layout.addWidget(self.title)
        
        top_layout.addStretch()
        self.btn_zoom_in = QPushButton("🔍 Zoom In (1 Cam)")
        self.btn_zoom_out = QPushButton("🔍 Zoom Out (4 Cams)")
        top_layout.addWidget(self.btn_zoom_in)
        top_layout.addWidget(self.btn_zoom_out)
        self.main_layout.addLayout(top_layout)
        
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(10)
        self.main_layout.addWidget(self.grid_container, stretch=1)
        
        self.btn_zoom_in.clicked.connect(self.zoom_in)
        self.btn_zoom_out.clicked.connect(self.zoom_out)
        
        self.build_grid()
        
        if self.camera_worker:
            self.camera_worker.frame_ready.connect(self.update_frame)

    def build_grid(self):
        for i in reversed(range(self.grid_layout.count())): 
            self.grid_layout.itemAt(i).widget().setParent(None)
        self.video_labels.clear()
        self.cam_statuses.clear()
        
        max_cams = 1 if self.zoom_level == 1 else 4
        cols = 1 if self.zoom_level == 1 else 2
        
        active_list = list(range(max_cams))
        if self.camera_worker:
            self.camera_worker.set_active_cameras(active_list)
            
        for i in range(max_cams):
            lbl = QLabel(f"Camera {i}\n(Scanning...)")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setMinimumSize(200, 150)
            lbl.setScaledContents(True) # ให้การ์ดจอช่วยวาดสเกลภาพ
            
            self.video_labels[i] = lbl
            self.cam_statuses[i] = None
            row, col = divmod(i, cols)
            self.grid_layout.addWidget(lbl, row, col)
            
        self.set_theme(self.current_theme_dark)

    def zoom_in(self):
        if self.zoom_level > 1:
            self.zoom_level = 1
            self.build_grid()

    def zoom_out(self):
        if self.zoom_level < 2:
            self.zoom_level = 2
            self.build_grid()

    def set_theme(self, is_dark_mode):
        self.current_theme_dark = is_dark_mode
        btn_style = f"background-color: {'#334155' if is_dark_mode else '#cbd5e1'}; color: {'white' if is_dark_mode else 'black'}; padding: 6px 12px; border-radius: 4px; font-weight: bold; border: none;"
        self.btn_zoom_in.setStyleSheet(btn_style)
        self.btn_zoom_out.setStyleSheet(btn_style)
        self.title.setStyleSheet(f"color: {'white' if is_dark_mode else 'black'}; font-size: 20px; font-weight: bold;")
        
        box_bg = "#0f172a" if is_dark_mode else "#e2e8f0"
        box_border = "#334155" if is_dark_mode else "#cbd5e1"
        
        for i, lbl in self.video_labels.items():
            self.cam_statuses[i] = None # ล้างแคชสไตล์ตอนเปลี่ยนโหมด
            lbl.setStyleSheet(f"background-color: {box_bg}; color: {'#94a3b8' if is_dark_mode else '#475569'}; font-weight: bold; border: 2px solid {box_border}; border-radius: 6px; font-size: 14px;")

    def update_frame(self, cam_index, cv_img):
        if cam_index in self.video_labels:
            lbl = self.video_labels[cam_index]
            bg_color = '#0f172a' if self.current_theme_dark else '#e2e8f0'
            border_color = '#334155' if self.current_theme_dark else '#cbd5e1'
            
            # 🟢 กล้องดับ -> ล็อกสไตล์ไม่ให้โหลดซ้ำซ้อน
            if cv_img is None:
                if self.cam_statuses[cam_index] == "offline": return
                self.cam_statuses[cam_index] = "offline"
                
                lbl.setPixmap(QPixmap())
                lbl.setText(f"Camera {cam_index}\n(Offline)")
                lbl.setStyleSheet(f"background-color: {bg_color}; color: #ef4444; font-weight: bold; border: 2px solid #ef4444; border-radius: 6px; font-size: 14px;")
                return
                
            # กล้องติดปกติ
            h, w, ch = cv_img.shape
            bytes_per_line = ch * w
            q_img = QImage(cv_img.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)
            
            if self.cam_statuses[cam_index] != "online":
                self.cam_statuses[cam_index] = "online"
                lbl.setText("")
                lbl.setStyleSheet(f"background-color: {bg_color}; border: 2px solid {border_color}; border-radius: 6px;")
            
            lbl.setPixmap(pixmap)