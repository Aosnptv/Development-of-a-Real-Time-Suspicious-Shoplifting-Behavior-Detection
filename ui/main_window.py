import sys
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QFrame, QLabel
from PySide6.QtCore import Qt, QTimer, QDateTime, Signal
from PySide6.QtGui import QFont

from ui.dashboard_page import DashboardPage
from ui.incident_history_page import IncidentHistoryPage  # ✅ หน้าประวัติ (ฟีเจอร์ใหม่)
from ui.multi_cam_page import MultiCamPage
from ui.playback_page import PlaybackPage  
from ui.settings_page import SettingsPage  
from services.camera_service import CameraWorker

try:
    import psutil
except ImportError:
    psutil = None

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
        self.resize(1350, 850) # ปรับขนาดให้รองรับหน้าจอที่เพิ่มขึ้นเล็กน้อย
        
        self.is_dark_mode = True 
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ==========================================
        # 1. SIDEBAR (แถบเมนูด้านซ้าย)
        # ==========================================
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
        
        # สร้างปุ่มเมนู (เพิ่มปุ่ม History เข้าไปในกลุ่ม)
        self.btn_dashboard = QPushButton("📊 Dashboard")
        self.btn_history = QPushButton("📋 Incident History") # ✅ แทรกเข้ามาตามสถาปัตยกรรม
        self.btn_multicam = QPushButton("📹 Multi-Cam Grid")
        self.btn_playback = QPushButton("⏪ Playback History")  
        self.btn_settings = QPushButton("⚙️ Settings")  
        
        # จัดเรียงลำดับปุ่มในแถบนำทาง (Navigation Buttons)
        self.nav_buttons = [
            self.btn_dashboard, 
            self.btn_history,    # Index 1
            self.btn_multicam,   # Index 2
            self.btn_playback,   # Index 3
            self.btn_settings    # Index 4
        ]
        
        for btn in self.nav_buttons:
            btn.setCheckable(True)
            sidebar_layout.addWidget(btn)
            
        self.btn_dashboard.setChecked(True)
        sidebar_layout.addStretch()
        
        # กรอบแสดงสถานะเครื่อง (Metrics) ด้านล่างสุดของ Sidebar
        self.metrics_frame = QFrame()
        metrics_lay = QVBoxLayout(self.metrics_frame)
        self.lbl_metrics = QLabel("Loading Metrics...")
        metrics_lay.addWidget(self.lbl_metrics)
        sidebar_layout.addWidget(self.metrics_frame)
        
        main_layout.addWidget(self.sidebar)
        
        # ==========================================
        # 2. WORKER & CORE SERVICES
        # ==========================================
        self.camera_worker = CameraWorker()
        self.camera_worker.start_camera()
        
        # เชื่อมต่อภาพสตรีมหลักเข้าหน้า Dashboard เดิม
        self.camera_worker.frame_ready.connect(self.update_dashboard_camera)
        
        # ==========================================
        # 3. PAGES REGISTRATION (ลงทะเบียนหน้าจอ)
        # ==========================================
        self.stacked_widget = QStackedWidget()
        
        # สร้าง Instance ของแต่ละหน้า (คงรูปแบบการเรียก DashboardPage แบบเดิมของคุณไว้)
        self.page_dashboard = DashboardPage(self.camera_worker)
        self.page_history = IncidentHistoryPage() # ✅ หน้าประวัติ (ฟีเจอร์ใหม่)
        
        # ผูกข้อมูลส่งไปให้หน้ามัลติแคมอ้างอิงผ่านตัวแม่ (คงของเดิมไว้)
        camera_dict = {}
        if self.camera_worker is not None:
            for idx in self.camera_worker.active_indices:
                camera_dict[idx] = self.camera_worker
            
        self.page_multicam = MultiCamPage(camera_dict)
        self.page_playback = PlaybackPage()
        self.page_settings = SettingsPage()
        
        # จัดเรียงตำแหน่งหน้าเข้า Stacked Widget (เรียงดัชนี Index 0-4)
        self.stacked_widget.addWidget(self.page_dashboard)  # Index 0
        self.stacked_widget.addWidget(self.page_history)    # Index 1 (แทรกใหม่)
        self.stacked_widget.addWidget(self.page_multicam)   # Index 2
        self.stacked_widget.addWidget(self.page_playback)   # Index 3
        self.stacked_widget.addWidget(self.page_settings)   # Index 4
        
        main_layout.addWidget(self.stacked_widget, stretch=1)
        
        # ==========================================
        # 4. SIGNALS & NAVIGATION CONNECTIONS
        # ==========================================
        # ผูกปุ่มกดเมนูกับการสลับหน้า
        self.btn_dashboard.clicked.connect(lambda: self._navigate_to(0, self.btn_dashboard))
        self.btn_history.clicked.connect(lambda: [
            self.page_history.load_data_from_db(), # ดึงข้อมูลล่าสุดจาก DB ทุกครั้งที่เปิดหน้านี้
            self._navigate_to(1, self.btn_history)
        ])
        self.btn_multicam.clicked.connect(lambda: self._navigate_to(2, self.btn_multicam))
        self.btn_playback.clicked.connect(lambda: self._navigate_to(3, self.btn_playback))
        self.btn_settings.clicked.connect(lambda: self._navigate_to(4, self.btn_settings))
        
        # ✅ เชื่อมสัญญาณตรวจจับพฤติกรรม (Incident) ไปอัปเดตหน้าประวัติแบบ Real-time
        if hasattr(self.camera_worker, 'incident_triggered'):
            self.camera_worker.incident_triggered.connect(self.page_history.load_data_from_db)
            if hasattr(self.page_dashboard, 'refresh_dashboard_data'):
                self.camera_worker.incident_triggered.connect(self.page_dashboard.refresh_dashboard_data)
        
        # ตั้งค่าตัวจับเวลาอัปเดต Metrics ระบบ
        self.sys_timer = QTimer()
        self.sys_timer.timeout.connect(self._update_system_stats)
        self.sys_timer.start(1000)
        
        # บังคับใช้ Theme เริ่มต้น
        self.apply_theme()

    # ==========================================
    # 5. THEME & SYSTEM FUNCTIONS (ฟังก์ชันเดิมทั้งหมด)
    # ==========================================
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
        
        # ส่งสถานะ Theme ไปให้อัปเดตที่หน้าต่างย่อยทุกหน้า
        self.page_dashboard.set_theme(self.is_dark_mode)
        if hasattr(self.page_history, 'set_theme'):
            self.page_history.set_theme(self.is_dark_mode)
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

            gpu_p = "N/A"
            if HAS_GPU:
                try:
                    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    gpu_p = f"{util.gpu}%"
                except Exception:
                    gpu_p = "Err"

            self.lbl_metrics.setText(f"🖥️ CPU: {cpu_p}%\n💾 RAM: {ram_p}%\n🎮 GPU: {gpu_p}\n⚡ FPS: {fps_val}\n🚨 Alerts: {alert_count}")
            
            is_danger = (alert_count > 0 or cpu_p > 85 or ram_p > 85 or (HAS_GPU and isinstance(gpu_p, int) and gpu_p > 85))
            color = "#ef4444" if is_danger else ("#4ade80" if self.is_dark_mode else "#16a34a")
            self.lbl_metrics.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: bold; background: transparent; line-height: 140%;")
        else:
            self.lbl_metrics.setText("Metrics N/A")

    def update_dashboard_camera(self, idx, frame):
        self.page_dashboard.update_camera_frame(idx, frame)

    def closeEvent(self, event):
        if hasattr(self, 'camera_worker'):
            self.camera_worker.stop_camera()
        if HAS_GPU:
            try: pynvml.nvmlShutdown()
            except Exception: pass
        event.accept()