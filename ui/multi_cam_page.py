from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                               QLabel, QPushButton, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap

class ClickableVideoLabel(QLabel):
    def __init__(self, cam_index, parent_page):
        super().__init__()
        self.cam_index = cam_index
        self.parent_page = parent_page
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(200, 150)
        self.setScaledContents(True)
        self.setMouseTracking(True)
        
        self.fps_label = QLabel("0.0 FPS", self)
        self.fps_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.fps_label.setStyleSheet("""
            background-color: rgba(0, 0, 0, 160); 
            color: #10b981; 
            font-weight: bold; 
            font-size: 12px; 
            padding: 3px 6px; 
            border-bottom-left-radius: 4px;
        """)
        self.fps_label.adjustSize()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fps_label.move(self.width() - self.fps_label.width(), 0)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.parent_page.handle_cam_double_click(self.cam_index)

class MultiCamPage(QWidget):
    def __init__(self, camera_workers_dict=None):
        super().__init__()
        self.workers = camera_workers_dict or {}
        self.zoom_level = 2  
        self.zoomed_cam_index = None
        self.video_labels = {}
        self.cam_statuses = {}
        self.current_theme_dark = True
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        
        top_layout = QHBoxLayout()
        self.title = QLabel("📹 Multi-Cam Grid View")
        self.title.setStyleSheet("font-size: 20px; font-weight: bold;")
        top_layout.addWidget(self.title)
        
        top_layout.addStretch()
        self.btn_zoom_out = QPushButton("📱 Show All Cams")
        top_layout.addWidget(self.btn_zoom_out)
        self.main_layout.addLayout(top_layout)
        
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(15)
        self.main_layout.addWidget(self.grid_container, stretch=1)
        
        self.control_panel = QFrame()
        self.control_panel.setFrameShape(QFrame.StyledPanel)
        self.panel_layout = QHBoxLayout(self.control_panel)
        self.panel_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.addWidget(self.control_panel)
        
        self.btn_zoom_out.clicked.connect(self.reset_zoom)
        
        self.build_grid()
        self.build_control_buttons()
        
        connected_workers = set()
        for cam_idx, worker in self.workers.items():
            if worker not in connected_workers:
                worker.frame_ready.connect(self.update_frame)
                if hasattr(worker, 'info_updated'):
                    try:
                        worker.info_updated.connect(self.update_cam_info)
                    except Exception:
                        pass
                connected_workers.add(worker)

    def build_grid(self):
        for i in reversed(range(self.grid_layout.count())): 
            self.grid_layout.itemAt(i).widget().setParent(None)
        self.video_labels.clear()
        
        if self.zoom_level == 1 and self.zoomed_cam_index is not None:
            lbl = ClickableVideoLabel(self.zoomed_cam_index, self)
            self.video_labels[self.zoomed_cam_index] = lbl
            self.grid_layout.addWidget(lbl, 0, 0)
        else:
            num_cams = len(self.workers) if len(self.workers) > 0 else 2
            cols = 2 if num_cams <= 4 else 3
            
            for i in range(num_cams):
                lbl = ClickableVideoLabel(i, self)
                self.video_labels[i] = lbl
                row, col = divmod(i, cols)
                self.grid_layout.addWidget(lbl, row, col)
                
        self.set_theme(self.current_theme_dark)

    def build_control_buttons(self):
        for i in reversed(range(self.panel_layout.count())):
            self.panel_layout.itemAt(i).widget().setParent(None)
            
        num_cams = len(self.workers) if len(self.workers) > 0 else 2
        
        for cam_idx in range(num_cams):
            cam_box = QWidget()
            box_lay = QHBoxLayout(cam_box)
            box_lay.setContentsMargins(0, 0, 0, 0)
            
            lbl_name = QLabel(f"กล้อง {cam_idx + 1}:")
            lbl_name.setStyleSheet("font-weight: bold;")
            
            btn_start = QPushButton("▶ Start")
            btn_stop = QPushButton("⏸ Stop")
            btn_reset = QPushButton("🔄 Restart")
            
            btn_start.clicked.connect(lambda checked=False, idx=cam_idx: self.control_worker(idx, "start"))
            btn_stop.clicked.connect(lambda checked=False, idx=cam_idx: self.control_worker(idx, "stop"))
            btn_reset.clicked.connect(lambda checked=False, idx=cam_idx: self.control_worker(idx, "restart"))
            
            box_lay.addWidget(lbl_name)
            box_lay.addWidget(btn_start)
            box_lay.addWidget(btn_stop)
            box_lay.addWidget(btn_reset)
            
            self.panel_layout.addWidget(cam_box)
            
    def control_worker(self, cam_idx, action):
        if cam_idx in self.workers:
            parent_worker = self.workers[cam_idx]
            if hasattr(parent_worker, 'sub_workers') and cam_idx in parent_worker.sub_workers:
                sub_worker = parent_worker.sub_workers[cam_idx]
                if action == "start": sub_worker.start_camera()
                elif action == "stop": sub_worker.stop_camera()
                elif action == "restart": sub_worker.restart_camera()

    def handle_cam_double_click(self, cam_index):
        if self.zoom_level == 2:
            self.zoom_level = 1
            self.zoomed_cam_index = cam_index
            self.title.setText(f"🔍 Viewing Camera {cam_index + 1} (Double Click to return)")
        else:
            self.zoom_level = 2
            self.zoomed_cam_index = None
            self.title.setText("📹 Multi-Cam Grid View")
        self.build_grid()

    def reset_zoom(self):
        self.zoom_level = 2
        self.zoomed_cam_index = None
        self.title.setText("📹 Multi-Cam Grid View")
        self.build_grid()

    def update_cam_info(self, cam_index, status, fps, width, height):
        if cam_index in self.video_labels:
            lbl = self.video_labels[cam_index]
            lbl.fps_label.setText(f"{fps:.1f} FPS")
            lbl.fps_label.adjustSize()
            lbl.fps_label.move(lbl.width() - lbl.fps_label.width(), 0)
            
            if status == "Online":
                lbl.setToolTip(f"🖥️ Resolution: {width} x {height}\n🟢 Status: {status}")
            else:
                lbl.setToolTip(f"🔴 Status: {status}")

            bg_color = '#0f172a' if self.current_theme_dark else '#e2e8f0'
            if status in ["Offline", "Stopped"]:
                if self.cam_statuses.get(cam_index) == status: return
                self.cam_statuses[cam_index] = status
                lbl.setPixmap(QPixmap())
                lbl.setText(f"Camera {cam_index + 1}\n({status})")
                text_color = "#ef4444" if status == "Offline" else "#f59e0b"
                lbl.setStyleSheet(f"background-color: {bg_color}; color: {text_color}; font-weight: bold; border: 2px solid {text_color}; border-radius: 6px; font-size: 14px;")

    def update_frame(self, cam_idx, frame):
        if frame is None:
            return
            
        if cam_idx in self.video_labels:
            lbl = self.video_labels[cam_idx]
            bg_color = '#0f172a' if self.current_theme_dark else '#e2e8f0'
            border_color = '#334155' if self.current_theme_dark else '#cbd5e1'
            
            if self.cam_statuses.get(cam_idx) != "online":
                self.cam_statuses[cam_idx] = "online"
                lbl.setText("")
                # เอาสีพื้นหลังออกเวลาภาพมาแล้ว เพื่อไม่ให้สีทับรูป
                lbl.setStyleSheet(f"border: 2px solid {border_color}; border-radius: 6px;")
            
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            
            # 🟢 เปลี่ยนจาก frame.data เป็น frame.tobytes() 
            q_img = QImage(frame.tobytes(), w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)
            
            if not pixmap.isNull():
                lbl.setPixmap(pixmap)
        if frame is None:
            return
            
        if cam_idx in self.video_labels:
            lbl = self.video_labels[cam_idx]
            bg_color = '#0f172a' if self.current_theme_dark else '#e2e8f0'
            border_color = '#334155' if self.current_theme_dark else '#cbd5e1'
            
            if self.cam_statuses.get(cam_idx) != "online":
                self.cam_statuses[cam_idx] = "online"
                lbl.setText("")
                lbl.setStyleSheet(f"background-color: {bg_color}; border: 2px solid {border_color}; border-radius: 6px;")
            
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)
            lbl.setPixmap(pixmap)

    def set_theme(self, is_dark_mode):
        self.current_theme_dark = is_dark_mode
        text_color = 'white' if is_dark_mode else 'black'
        self.title.setStyleSheet(f"color: {text_color}; font-size: 20px; font-weight: bold;")
        
        box_bg = "#0f172a" if is_dark_mode else "#e2e8f0"
        box_border = "#334155" if is_dark_mode else "#cbd5e1"
        
        self.control_panel.setStyleSheet(f"background-color: {'#1e293b' if is_dark_mode else '#f1f5f9'}; border: 1px solid {box_border}; border-radius: 8px;")
        
        for btn in self.control_panel.findChildren(QPushButton):
            btn.setStyleSheet(f"background-color: {'#334155' if is_dark_mode else '#cbd5e1'}; color: {text_color}; padding: 5px 10px; border-radius: 4px; border: none; font-weight: bold;")

        for i, lbl in self.video_labels.items():
            if self.cam_statuses.get(i) != "online":
                status = self.cam_statuses.get(i, "Scanning...")
                text_color_lbl = "#ef4444" if status == "Offline" else ("#f59e0b" if status == "Stopped" else "#94a3b8")
                lbl.setStyleSheet(f"background-color: {box_bg}; color: {text_color_lbl}; font-weight: bold; border: 2px solid {box_border}; border-radius: 6px; font-size: 14px;")