# ui/dashboard_page.py
import os
import cv2
import pandas as pd
import numpy as np  # 🟢 จุดสำคัญ: เพิ่มเข้ามาเพื่อรองรับคำสั่ง np.ascontiguousarray
from datetime import datetime
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QPixmap, QImage
from services.database_service import DatabaseService

class DashboardPage(QWidget):
    def __init__(self, camera_worker=None, parent=None):
        super().__init__(parent)
        self.camera_worker = camera_worker
        self.db = DatabaseService()
        self.is_dark_theme = True
        self.cam_statuses = {0: None, 1: None} # จดจำสถานะเพื่อลดภาระ CPU

        self.setup_ui()
        self.refresh_dashboard_data()

        # ตั้งเวลาให้รีเฟรชตัวเลขสถิติและรูปภาพเหตุการณ์ล่าสุด ทุกๆ 3 วินาที
        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self.refresh_dashboard_data)
        self.stats_timer.start(3000)

    def setup_ui(self):
        """สร้างโครงสร้างหน้าต่างเมนูหลักแบบไม่มีโค้ดซ้ำซ้อน"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # ==========================================
        # 1. แถวบน: การ์ดแสดงสถิติ (วันนี้ / ทั้งหมด)
        # ==========================================
        stats_layout = QHBoxLayout()
        
        self.card_today = QFrame()
        self.card_today.setFrameShape(QFrame.StyledPanel)
        today_layout = QVBoxLayout(self.card_today)
        self.lbl_today_title = QLabel("🚨 แจ้งเตือนวันนี้")
        self.lbl_today_title.setAlignment(Qt.AlignCenter)
        self.lbl_today_count = QLabel("0")
        self.lbl_today_count.setAlignment(Qt.AlignCenter)
        self.lbl_today_count.setStyleSheet("font-size: 36px; font-weight: bold; color: #ef4444;")
        today_layout.addWidget(self.lbl_today_title)
        today_layout.addWidget(self.lbl_today_count)

        self.card_total = QFrame()
        self.card_total.setFrameShape(QFrame.StyledPanel)
        total_layout = QVBoxLayout(self.card_total)
        self.lbl_total_title = QLabel("📁 แจ้งเตือนทั้งหมด")
        self.lbl_total_title.setAlignment(Qt.AlignCenter)
        self.lbl_total_count = QLabel("0")
        self.lbl_total_count.setAlignment(Qt.AlignCenter)
        self.lbl_total_count.setStyleSheet("font-size: 36px; font-weight: bold; color: #3b82f6;")
        total_layout.addWidget(self.lbl_total_title)
        total_layout.addWidget(self.lbl_total_count)

        stats_layout.addWidget(self.card_today)
        stats_layout.addWidget(self.card_total)
        main_layout.addLayout(stats_layout, stretch=1)

        # ==========================================
        # 2. แถวล่าง: แบ่งฝั่ง [กล้องสด 2 ตัว] | [หลักฐานล่าสุด 3 รูป]
        # ==========================================
        content_layout = QHBoxLayout()

        # --- ฝั่งซ้าย: หน้าจอวิดีโอกล้องสด ---
        cam_layout = QVBoxLayout()
        self.lbl_cam_title = QLabel("📹 ระบบสตรีมมิ่งกล้องวงจรปิดสด (Live Camera)")
        self.lbl_cam_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        cam_layout.addWidget(self.lbl_cam_title)
        
        self.lbl_cam1 = QLabel("รอสัญญาณกล้อง 1...")
        self.lbl_cam1.setAlignment(Qt.AlignCenter)
        self.lbl_cam1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.lbl_cam1.setStyleSheet("background-color: black; color: white; border-radius: 6px;")
        
        self.lbl_cam2 = QLabel("รอสัญญาณกล้อง 2...")
        self.lbl_cam2.setAlignment(Qt.AlignCenter)
        self.lbl_cam2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.lbl_cam2.setStyleSheet("background-color: black; color: white; border-radius: 6px;")

        cam_layout.addWidget(self.lbl_cam1, stretch=1)
        cam_layout.addWidget(self.lbl_cam2, stretch=1)
        content_layout.addLayout(cam_layout, stretch=7) # ให้ฝั่งกล้องกินพื้นที่ส่วนใหญ่ของจอ

        # --- ฝั่งขวา: แผงโชว์ภาพหลักฐาน 3 รายการล่าสุด ---
        right_panel = QWidget()
        right_panel.setFixedWidth(340) 
        latest_layout = QVBoxLayout(right_panel)
        latest_layout.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_latest_title = QLabel("🔴 ประวัติล่าสุด (3 รายการ)")
        self.lbl_latest_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        latest_layout.addWidget(self.lbl_latest_title)

        self.evidence_images = []
        self.evidence_details = []

        for i in range(3):
            img_lbl = QLabel("รอข้อมูล...")
            img_lbl.setAlignment(Qt.AlignCenter)
            img_lbl.setFixedSize(320, 200)
            img_lbl.setFrameShape(QFrame.Box)
            
            detail_lbl = QLabel("-")
            detail_lbl.setWordWrap(True)
            detail_lbl.setStyleSheet("font-size: 14px;")
            
            latest_layout.addWidget(img_lbl)
            latest_layout.addWidget(detail_lbl)
            
            self.evidence_images.append(img_lbl)
            self.evidence_details.append(detail_lbl)

        latest_layout.addStretch()
        content_layout.addWidget(right_panel, alignment=Qt.AlignRight | Qt.AlignTop)

        main_layout.addLayout(content_layout, stretch=9)
        self.set_theme(self.is_dark_theme)

    def refresh_dashboard_data(self):
        """ดึงข้อมูลสถิติและรูปภาพ 3 ล่าสุดจาก SQLite มาอัปเดตแบบเรียลไทม์"""
        try:
            df = self.db.get_recent_alerts(limit=1000)
            
            if df.empty:
                self.lbl_total_count.setText("0")
                self.lbl_today_count.setText("0")
                return

            # คำนวณยอดแจ้งเตือนทั้งหมด และเฉพาะของวันนี้
            total_alerts = len(df)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            today_date = datetime.now().date()
            today_alerts = len(df[df['timestamp'].dt.date == today_date])
            
            self.lbl_total_count.setText(f"{total_alerts}")
            self.lbl_today_count.setText(f"{today_alerts}")

            # โหลดภาพนิ่งหลักฐาน 3 รายการล่าสุดมาชิดขวาจอ
            now = datetime.now()
            display_count = min(3, len(df))

            for i in range(3):
                if i < display_count:
                    alert = df.iloc[i]
                    img_path = alert['image_path']
                    cam_id = alert['camera_id']
                    timestamp = alert['timestamp']

                    time_diff = now - timestamp
                    seconds = time_diff.total_seconds()
                    if seconds < 60: time_ago = f"{int(seconds)} วิ"
                    elif seconds < 3600: time_ago = f"{int(seconds // 60)} นาที"
                    else: time_ago = f"{int(seconds // 3600)} ชม."

                    detail_text = f"📷 กล้อง {cam_id + 1} | ⏰ {timestamp.strftime('%H:%M:%S')} ({time_ago}ที่แล้ว)"
                    self.evidence_details[i].setText(detail_text)

                    if img_path and os.path.exists(img_path):
                        pixmap = QPixmap(img_path)
                        scaled = pixmap.scaled(320, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        self.evidence_images[i].setPixmap(scaled)
                    else:
                        self.evidence_images[i].clear()
                        self.evidence_images[i].setText("❌ ไม่พบไฟล์ภาพหลักฐาน")
                else:
                    self.evidence_images[i].clear()
                    self.evidence_images[i].setText("-")
                    self.evidence_details[i].setText("-")

        except Exception as e:
            print(f"❌ Error refreshing dashboard: {e}")

    def update_camera_frame(self, cam_idx, cv_img):
        """รับสัญญาณภาพวิดีโอสด และแสดงผลลัพธ์บน UI อย่างถูกต้อง"""
        if cam_idx not in [0, 1]:
            return
            
        target_lbl = self.lbl_cam1 if cam_idx == 0 else self.lbl_cam2

        if cv_img is None:
            if self.cam_statuses.get(cam_idx) == "offline": 
                return
            self.cam_statuses[cam_idx] = "offline"
            target_lbl.clear()
            target_lbl.setText(f"⚠️ กล้อง {cam_idx + 1} ขาดการเชื่อมต่อ")
            target_lbl.setStyleSheet("background-color: black; color: white; border-radius: 6px; font-weight: bold;")
            return

        self.cam_statuses[cam_idx] = "online"
        
        try:
            # บังคับให้จัดเรียง Array ป้องกันปัญหาภาพหายหรือเบลอใน PySide6
            cv_img = np.ascontiguousarray(cv_img)
            h, w, ch = cv_img.shape
            bytes_per_line = ch * w
            
            lbl_size = target_lbl.size()
            if lbl_size.width() <= 10 or lbl_size.height() <= 10:
                lbl_size = QSize(520, 350)
                
            q_img = QImage(cv_img.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img.copy()).scaled(lbl_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            target_lbl.setPixmap(pixmap)
        except Exception as e:
            print(f"❌ Error processing camera frame {cam_idx}: {e}")
            
    def set_theme(self, is_dark_mode):
        """ปรับแต่งคู่สีมาตรฐาน (Light / Dark Mode) สบายตาและถูกต้องตามหลักสถาปัตยกรรมระบบ UI"""
        self.is_dark_theme = is_dark_mode
        text_color = "white" if is_dark_mode else "#0f172a"
        bg_color = "#1e293b" if is_dark_mode else "#ffffff"
        border_color = "#334155" if is_dark_mode else "#cbd5e1"
        img_bg = "#0f172a" if is_dark_mode else "#f8fafc"
        sub_text_color = "#94a3b8" if is_dark_mode else "#475569"

        # ตั้งค่าสไตล์ให้การ์ดตัวเลขด้านบน
        card_style = f"background-color: {bg_color}; border: 1px solid {border_color}; border-radius: 8px;"
        self.card_today.setStyleSheet(card_style)
        self.card_total.setStyleSheet(card_style)

        # สไตล์ของหัวข้อต่างๆ
        title_style = f"color: {text_color}; font-size: 16px; font-weight: bold; background: transparent;"
        self.lbl_today_title.setStyleSheet(title_style)
        self.lbl_total_title.setStyleSheet(title_style)
        self.lbl_cam_title.setStyleSheet(title_style)
        self.lbl_latest_title.setStyleSheet(title_style)
        
        # ปรับการแสดงผลแผงข้อมูลด้านขวา
        for lbl in self.evidence_details:
            lbl.setStyleSheet(f"color: {sub_text_color}; font-size: 13px; margin-bottom: 8px; font-weight: bold; background: transparent;")
        
        for img in self.evidence_images:
            img.setStyleSheet(f"background-color: {img_bg}; color: {text_color}; border: 1px solid {border_color}; border-radius: 6px;")