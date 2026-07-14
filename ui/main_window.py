import sys
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QFrame, QLabel
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QFont

from ui.dashboard_page import DashboardPage
from ui.multi_cam_page import MultiCamPage
from ui.playback_page import PlaybackPage  
from ui.settings_page import SettingsPage  
from services.camera_service import CameraWorker

try:
    import psutil
except ImportError:
    psutil = None

# 🟢 พยายามดึงฟังก์ชันวัดการทำงานของการ์ดจอ (NVIDIA GPU Monitor)
try:
    import pynvml
    pynvml.nvmlInit()
    HAS_GPU = True
except Exception:
    HAS_GPU = False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Suspicious Behavior Detection System")
        self.resize(1300, 780)
        
        self.is_dark_mode = True 
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # SIDEBAR
        self.sidebar = QFrame()
        self.sidebar.setMinimumWidth(240)
        self.sidebar.setMaximumWidth(240)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(16, 24, 16, 24)
        sidebar_layout.setSpacing(10)
        
        self.lbl_title = QLabel("👁️ AI SHIELD")
        self.lbl_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        sidebar_layout.addWidget(self.lbl_title)
        
        self.lbl_datetime = QLabel()
        self.lbl_datetime.setStyleSheet("color: #38bdf8; font-size: 12px; font-weight: bold; padding-bottom: 10px;")
        sidebar_layout.addWidget(self.lbl_datetime)
        
        self.btn_theme = QPushButton("🌓 Switch Light/Dark")
        self.btn_theme.setStyleSheet("background-color: #f59e0b; color: white; padding: 8px; border-radius: 6px; font-weight: bold; border: none;")
        self.btn_theme.clicked.connect(self.toggle_theme)
        sidebar_layout.addWidget(self.btn_theme)
        
        self.btn_dashboard = QPushButton("📊 Dashboard")
        self.btn_multicam = QPushButton("📹 Multi-Cam Grid")
        self.btn_playback = QPushButton("⏪ Playback History")  
        self.btn_settings = QPushButton("⚙️ Settings")  
        
        self.nav_buttons = [self.btn_dashboard, self.btn_multicam, self.btn_playback, self.btn_settings]
        for btn in self.nav_buttons:
            btn.setCheckable(True)
            sidebar_layout.addWidget(btn)
            
        self.btn_dashboard.setChecked(True)
        sidebar_layout.addStretch()
        
        self.metrics_frame = QFrame()
        metrics_lay = QVBoxLayout(self.metrics_frame)
        self.lbl_metrics = QLabel("Loading Metrics...")
        metrics_lay.addWidget(self.lbl_metrics)
        sidebar_layout.addWidget(self.metrics_frame)
        
        main_layout.addWidget(self.sidebar)
        
        # WORKER & PAGES
        self.camera_worker = CameraWorker()
        self.camera_worker.start_camera()
        
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
        
        self.btn_dashboard.clicked.connect(lambda: self._navigate_to(0, self.btn_dashboard))
        self.btn_multicam.clicked.connect(lambda: self._navigate_to(1, self.btn_multicam))
        self.btn_playback.clicked.connect(lambda: self._navigate_to(2, self.btn_playback))
        self.btn_settings.clicked.connect(lambda: self._navigate_to(3, self.btn_settings))
        
        self.sys_timer = QTimer()
        self.sys_timer.timeout.connect(self._update_system_stats)
        self.sys_timer.start(1000)
        
        self.apply_theme()

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()

    def apply_theme(self):
        bg_main = "#0f172a" if self.is_dark_mode else "#f8fafc"
        bg_sidebar = "#1e293b" if self.is_dark_mode else "#ffffff"
        text_main = "#ffffff" if self.is_dark_mode else "#0f172a"
        text_sidebar = "#94a3b8" if self.is_dark_mode else "#475569"
        btn_active = "#3b82f6" if self.is_dark_mode else "#2563eb"
        metrics_bg = "#334155" if self.is_dark_mode else "#e2e8f0"
        border = "#334155" if self.is_dark_mode else "#cbd5e1"

        self.setStyleSheet(f"QMainWindow {{ background-color: {bg_main}; }} QWidget {{ color: {text_main}; }}")
        self.sidebar.setStyleSheet(f"background-color: {bg_sidebar}; border-right: 1px solid {border};")
        self.lbl_title.setStyleSheet(f"color: {text_main}; background: transparent;")
        
        btn_style = f"""
            QPushButton {{ background-color: transparent; color: {text_sidebar}; border: none; border-radius: 6px; padding: 12px; font-weight: bold; text-align: left; }}
            QPushButton:hover {{ background-color: {metrics_bg}; color: {text_main}; }}
            QPushButton:checked {{ background-color: {btn_active}; color: #ffffff; }}
        """
        for btn in self.nav_buttons:
            btn.setStyleSheet(btn_style)

        self.metrics_frame.setStyleSheet(f"background-color: {metrics_bg}; border: 1px solid {border}; border-radius: 6px;")
        
        self.page_dashboard.set_theme(self.is_dark_mode)
        self.page_multicam.set_theme(self.is_dark_mode)
        self.page_playback.set_theme(self.is_dark_mode)
        self.page_settings.set_theme(self.is_dark_mode)

    def _navigate_to(self, page_index, active_btn):
        for btn in self.nav_buttons:
            btn.setChecked(False)
        active_btn.setChecked(True)
        self.stacked_widget.setCurrentIndex(page_index)
        
    def _update_system_stats(self):
        self.lbl_datetime.setText(f"📅 {QDateTime.currentDateTime().toString('dd MMM yyyy - hh:mm:ss')}")
        if psutil:
            cpu_p = psutil.cpu_percent()
            ram_p = psutil.virtual_memory().percent
            fps_val = getattr(self.camera_worker, 'current_fps', 30)
            alert_count = getattr(self.page_dashboard, 'total_alerts', 0)

            # 🟢 ดึงข้อมูลเปอร์เซ็นต์การทำงานของ GPU จริงออกมาใช้งาน
            gpu_p = "N/A"
            if HAS_GPU:
                try:
                    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    gpu_p = f"{util.gpu}%"
                except Exception:
                    gpu_p = "Err"

            # 🟢 เพิ่มการแสดงผลช่อง GPU: เข้าไปที่กล่องข้อความ
            self.lbl_metrics.setText(f"🖥️ CPU: {cpu_p}%\n💾 RAM: {ram_p}%\n🎮 GPU: {gpu_p}\n⚡ FPS: {fps_val}\n🚨 Alerts: {alert_count}")
            
            # เช็คความร้อนขีดอันตราย
            is_danger = (alert_count > 0 or cpu_p > 85 or ram_p > 85 or (HAS_GPU and isinstance(gpu_p, int) and gpu_p > 85))
            color = "#ef4444" if is_danger else ("#4ade80" if self.is_dark_mode else "#16a34a")
            self.lbl_metrics.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: bold; background: transparent; line-height: 140%;")
        else:
            self.lbl_metrics.setText("Metrics N/A")

    def closeEvent(self, event):
        self.camera_worker.stop_camera()
        if HAS_GPU:
            try: pynvml.nvmlShutdown()
            except Exception: pass
        event.accept()