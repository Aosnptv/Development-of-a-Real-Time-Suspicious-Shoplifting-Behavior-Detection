# ui/main_window.py
import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QStackedWidget, QFrame, QLabel)
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QFont

# นำเข้าทุกหน้าเพจให้ครบถ้วน
from ui.dashboard_page import DashboardPage
from ui.multi_cam_page import MultiCamPage
from ui.playback_page import PlaybackPage  
from ui.settings_page import SettingsPage  
from services.camera_service import CameraWorker

# ป้องกันระบบพังหากเครื่องผู้ใช้ไม่มีโมดูล psutil สำหรับคำนวณ CPU
try:
    import psutil
except ImportError:
    psutil = None

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Suspicious Behavior & Shoplifting Detection System")
        self.resize(1300, 750)
        self.setMinimumSize(1024, 680)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ─────────────── SIDEBAR NAVIGATION ───────────────
        sidebar = QFrame()
        sidebar.setStyleSheet("background-color: #0f172a; min-width: 240px; max-width: 240px;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 24, 16, 24)
        sidebar_layout.setSpacing(10)
        
        title_lbl = QLabel("👁️ AI SHIELD")
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #ffffff; padding-bottom: 10px;")
        sidebar_layout.addWidget(title_lbl)
        
        # วิดเจ็ตแสดงวันเวลาดิจิตอล
        self.lbl_datetime = QLabel()
        self.lbl_datetime.setStyleSheet("color: #38bdf8; font-size: 12px; font-weight: bold; padding-bottom: 15px;")
        sidebar_layout.addWidget(self.lbl_datetime)
        
        # สร้างชุดปุ่มกดเมนูให้ครบทั้ง 4 เพจ
        self.btn_dashboard = QPushButton("📊 Dashboard Overview")
        self.btn_multicam = QPushButton("📹 Multi-Cam Grid")
        self.btn_playback = QPushButton("⏪ Playback History")  
        self.btn_settings = QPushButton("⚙️ Telegram Settings")  
        
        btn_style = """
            QPushButton {
                background-color: transparent; color: #94a3b8; border: none;
                border-radius: 6px; padding: 12px 16px; font-size: 13px;
                font-weight: bold; text-align: left;
            }
            QPushButton:hover { background-color: #1e293b; color: #ffffff; }
            QPushButton:checked { background-color: #2563eb; color: #ffffff; }
        """
        
        self.nav_buttons = [self.btn_dashboard, self.btn_multicam, self.btn_playback, self.btn_settings]
        for btn in self.nav_buttons:
            btn.setStyleSheet(btn_style)
            btn.setCheckable(True)
            sidebar_layout.addWidget(btn)
            
        self.btn_dashboard.setChecked(True)
        sidebar_layout.addStretch()
        
        # ─────────────── SYSTEM METRICS BLOCK ───────────────
        # แสดงสถานะการทำงาน CPU ท้าย Sidebar
        metrics_frame = QFrame()
        metrics_frame.setStyleSheet("background-color: #1e293b; border-radius: 6px; padding: 8px;")
        metrics_lay = QVBoxLayout(metrics_frame)
        
        self.lbl_cpu = QLabel("CPU Usage: Fetching...")
        self.lbl_cpu.setStyleSheet("color: #4ade80; font-size: 11px; font-weight: bold;")
        metrics_lay.addWidget(self.lbl_cpu)
        
        sidebar_layout.addWidget(metrics_frame)
        
        version_lbl = QLabel("System v1.0.0 Ready")
        version_lbl.setStyleSheet("color: #475569; font-size: 11px; text-align: center;")
        sidebar_layout.addWidget(version_lbl)
        main_layout.addWidget(sidebar)
        
        # เรียกเปิดใช้งานระบบประมวลผลกล้องส่วนกลาง
        self.camera_worker = CameraWorker()
        self.camera_worker.start_camera()
        
        # ─────────────── STACKED PAGES AREA ───────────────
        self.stacked_widget = QStackedWidget()
        self.page_dashboard = DashboardPage(self.camera_worker)
        self.page_multicam = MultiCamPage(self.camera_worker)
        self.page_playback = PlaybackPage()  
        self.page_settings = SettingsPage()  
        
        self.stacked_widget.addWidget(self.page_dashboard)
        self.stacked_widget.addWidget(self.page_multicam)
        self.stacked_widget.addWidget(self.page_playback) 
        self.stacked_widget.addWidget(self.page_settings) 
        main_layout.addWidget(self.stacked_widget, stretch=1)
        
        # ผูกสัญญาณปุ่มนำทาง
        self.btn_dashboard.clicked.connect(lambda: self._navigate_to(0, self.btn_dashboard))
        self.btn_multicam.clicked.connect(lambda: self._navigate_to(1, self.btn_multicam))
        self.btn_playback.clicked.connect(lambda: self._navigate_to(2, self.btn_playback))
        self.btn_settings.clicked.connect(lambda: self._navigate_to(3, self.btn_settings))
        
        # ตัวควบคุมไทม์เมอร์อัปเดต เวลา และ ค่า CPU ทุกๆ 1 วินาที
        self.sys_timer = QTimer()
        self.sys_timer.timeout.connect(self._update_system_stats)
        self.sys_timer.start(1000)
        self._update_system_stats()

    def _navigate_to(self, page_index, active_btn):
        # ล้างสถานะปุ่มอื่น ให้ปุ่มที่กดปุ่มเดียวเปลี่ยนสีไฮไลท์
        for btn in self.nav_buttons:
            btn.setChecked(False)
        active_btn.setChecked(True)
        self.stacked_widget.setCurrentIndex(page_index)
        
    def _update_system_stats(self):
        # 1. อัปเดตเวลาประจำวัน
        current_dt = QDateTime.currentDateTime().toString("dd MMM yyyy - hh:mm:ss")
        self.lbl_datetime.setText(f"📅 {current_dt}")
        
        # 2. อัปเดตการอ่านค่า CPU จริงจากระบบปฏิบัติการ (แก้ไขคำสั่งที่ถูกต้องแล้ว)
        if psutil:
            cpu_p = psutil.cpu_percent()  # 🟢 แก้ไขจาก cpu_percentage() เป็น cpu_percent() เรียบร้อยครับ
            self.lbl_cpu.setText(f"🖥️ CPU Usage: {cpu_p}%")
            if cpu_p > 80:
                self.lbl_cpu.setStyleSheet("color: #ef4444; font-size: 11px; font-weight: bold;") 
            else:
                self.lbl_cpu.setStyleSheet("color: #4ade80; font-size: 11px; font-weight: bold;")
        else:
            self.lbl_cpu.setText("🖥️ CPU Usage: N/A (psutil missing)")

    def closeEvent(self, event):
        self.camera_worker.stop_camera()
        event.accept()