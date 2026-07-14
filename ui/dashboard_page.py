from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap

class DashboardPage(QWidget):
    def __init__(self, camera_worker):
        super().__init__()
        self.camera_worker = camera_worker
        self.total_alerts = 0
        self.is_dark_theme = True
        
        # 🟢 เพิ่มตัวจำสถานะเพื่อล็อกไม่ให้สั่งเขียน Stylesheet ซ้ำซากจน CPU ทะลุ 100%
        self.cam1_status = None 
        self.cam2_status = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # การ์ดสถิติ
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        self.card1, self.lbl_t1, self.lbl_v1 = self._create_stat_card("Total Detections", "1,240", "#3b82f6")
        self.card2, self.lbl_t2, self.lbl_v2 = self._create_stat_card("Suspicious Behavior", "42", "#f59e0b")
        self.card3, self.lbl_t3, self.lbl_v3 = self._create_stat_card("Shoplifting Alerts", "12", "#ef4444")
        stats_layout.addWidget(self.card1)
        stats_layout.addWidget(self.card2)
        stats_layout.addWidget(self.card3)
        layout.addLayout(stats_layout)
        
        # จอกล้อง
        video_layout = QHBoxLayout()
        video_layout.setSpacing(15)
        cam_items = [f"Camera {i}" for i in range(4)]
        
        # จอซ้าย
        cam1_frame = QVBoxLayout()
        self.combo_cam1 = QComboBox()
        self.combo_cam1.addItems(cam_items)
        self.lbl_video1 = QLabel("No Signal (Cam 1)")
        self.lbl_video1.setAlignment(Qt.AlignCenter)
        self.lbl_video1.setMinimumSize(400, 300)
        self.lbl_video1.setScaledContents(True) # 🟢 ให้การ์ดจอช่วยสเกลภาพแทน CPU
        cam1_frame.addWidget(self.combo_cam1)
        cam1_frame.addWidget(self.lbl_video1)
        video_layout.addLayout(cam1_frame)
        
        # จอขวา
        cam2_frame = QVBoxLayout()
        self.combo_cam2 = QComboBox()
        self.combo_cam2.addItems(cam_items)
        self.combo_cam2.setCurrentIndex(1)
        self.lbl_video2 = QLabel("No Signal (Cam 2)")
        self.lbl_video2.setAlignment(Qt.AlignCenter)
        self.lbl_video2.setMinimumSize(400, 300)
        self.lbl_video2.setScaledContents(True) # 🟢 ให้การ์ดจอช่วยสเกลภาพแทน CPU
        cam2_frame.addWidget(self.combo_cam2)
        cam2_frame.addWidget(self.lbl_video2)
        video_layout.addLayout(cam2_frame)
        
        layout.addLayout(video_layout, stretch=1)

        if self.camera_worker:
            self.camera_worker.frame_ready.connect(self.update_frame)
        self.combo_cam1.currentIndexChanged.connect(self.update_active_cameras)
        self.combo_cam2.currentIndexChanged.connect(self.update_active_cameras)
        self.update_active_cameras()

    def _create_stat_card(self, title, value, color):
        card = QFrame()
        card.setFixedHeight(90)
        lay = QVBoxLayout(card)
        lbl_title = QLabel(title)
        lbl_val = QLabel(value)
        lay.addWidget(lbl_title)
        lay.addWidget(lbl_val)
        return card, lbl_title, lbl_val

    def set_theme(self, is_dark_mode):
        self.is_dark_theme = is_dark_mode
        card_bg = "#1e293b" if is_dark_mode else "#ffffff"
        title_color = "#94a3b8" if is_dark_mode else "#64748b"
        val_colors = ["#3b82f6", "#f59e0b", "#ef4444"]
        border_color = "#334155" if is_dark_mode else "#cbd5e1"
        
        for i, (card, lbl_t, lbl_v) in enumerate([(self.card1, self.lbl_t1, self.lbl_v1), 
                                                   (self.card2, self.lbl_t2, self.lbl_v2), 
                                                   (self.card3, self.lbl_t3, self.lbl_v3)]):
            card.setStyleSheet(f"background-color: {card_bg}; border-radius: 8px; border-left: 5px solid {val_colors[i]}; border-top: 1px solid {border_color}; border-right: 1px solid {border_color}; border-bottom: 1px solid {border_color};")
            lbl_t.setStyleSheet(f"color: {title_color}; font-size: 12px; font-weight: bold; background: transparent;")
            lbl_v.setStyleSheet(f"color: {val_colors[i]}; font-size: 24px; font-weight: bold; background: transparent;")
            
        cb_style = f"background-color: {card_bg}; color: {'white' if is_dark_mode else 'black'}; padding: 6px; border: 1px solid {border_color}; border-radius: 4px;"
        self.combo_cam1.setStyleSheet(cb_style)
        self.combo_cam2.setStyleSheet(cb_style)
        
        # บังคับรีเซ็ตสถานะธีมเพื่อให้วาดหน้าจอใหม่ถูกต้อง
        self.cam1_status = None
        self.cam2_status = None

    def update_active_cameras(self):
        if self.camera_worker:
            try:
                idx1 = int(self.combo_cam1.currentText().split()[-1])
                idx2 = int(self.combo_cam2.currentText().split()[-1])
                self.camera_worker.set_active_cameras([idx1, idx2])
            except Exception:
                pass

    def update_frame(self, cam_index, cv_img):
        try:
            idx1 = int(self.combo_cam1.currentText().split()[-1])
            idx2 = int(self.combo_cam2.currentText().split()[-1])
            
            bg_color = '#0f172a' if self.is_dark_theme else '#e2e8f0'
            border_color = '#334155' if self.is_dark_theme else '#cbd5e1'
            fg_color = 'white' if self.is_dark_theme else 'black'
            
            # 🟢 กรณีกล้องดับ (ตรวจสอบ Cache เพื่อไม่ให้เขียนคำสั่งซ้ำรัวๆ)
            if cv_img is None:
                if cam_index == idx1 and self.cam1_status == "offline": return
                if cam_index == idx2 and self.cam2_status == "offline": return
                
                offline_style = f"background-color: {bg_color}; color: #ef4444; font-weight: bold; font-size: 14px; border: 2px solid #ef4444; border-radius: 8px;"
                if cam_index == idx1:
                    self.cam1_status = "offline"
                    self.lbl_video1.setPixmap(QPixmap())
                    self.lbl_video1.setText(f"⚠️ Camera {cam_index}\n(Offline / No Signal)")
                    self.lbl_video1.setStyleSheet(offline_style)
                if cam_index == idx2:
                    self.cam2_status = "offline"
                    self.lbl_video2.setPixmap(QPixmap())
                    self.lbl_video2.setText(f"⚠️ Camera {cam_index}\n(Offline / No Signal)")
                    self.lbl_video2.setStyleSheet(offline_style)
                return

            # กรณีกล้องติดปกติ
            h, w, ch = cv_img.shape
            bytes_per_line = ch * w
            q_img = QImage(cv_img.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)
            
            if cam_index == idx1:
                if self.cam1_status != "online":
                    self.cam1_status = "online"
                    self.lbl_video1.setText("")
                    self.lbl_video1.setStyleSheet(f"background-color: {bg_color}; border: 2px solid {border_color}; border-radius: 8px;")
                self.lbl_video1.setPixmap(pixmap)
                
            if cam_index == idx2:
                if self.cam2_status != "online":
                    self.cam2_status = "online"
                    self.lbl_video2.setText("")
                    self.lbl_video2.setStyleSheet(f"background-color: {bg_color}; border: 2px solid {border_color}; border-radius: 8px;")
                self.lbl_video2.setPixmap(pixmap)
        except Exception:
            pass