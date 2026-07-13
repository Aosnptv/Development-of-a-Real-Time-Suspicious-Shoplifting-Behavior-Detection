# ui/main_window.py
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QStackedWidget, QLabel, QFrame
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from ui.dashboard_page import DashboardPage
from ui.multi_cam_page import MultiCamPage
from ui.gallery_page import GalleryPage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real-Time Suspicious Behavior Detection Platform")
        self.resize(1280, 720)
        
        main_widget = QWidget()
        main_widget.setStyleSheet("background-color: #f1f5f9;")
        self.setCentralWidget(main_widget)
        
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # ─────────────── SIDEBAR MENU ───────────────
        sidebar = QFrame()
        sidebar.setFixedWidth(260)
        sidebar.setStyleSheet("background-color: #ffffff; border-right: 1px solid #e2e8f0;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 24, 16, 24)
        sidebar_layout.setSpacing(8)
        
        brand = QLabel("VISION CORE SYSTEM")
        brand.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        brand.setStyleSheet("color: #1e40af; letter-spacing: 1px; padding-left: 8px; margin-bottom: 20px;")
        sidebar_layout.addWidget(brand)
        
        btn_style = """
            QPushButton {
                text-align: left; padding: 12px 16px; background-color: transparent;
                border: none; border-radius: 6px; font-weight: bold; color: #475569; font-size: 13px;
            }
            QPushButton:hover { background-color: #f1f5f9; color: #0f172a; }
            QPushButton:checked { background-color: #eff6ff; color: #2563eb; border-left: 4px solid #2563eb; }
        """
        
        self.btn_dash = QPushButton("Overview Dashboard")
        self.btn_dash.setCheckable(True)
        self.btn_dash.setStyleSheet(btn_style)
        
        self.btn_multi = QPushButton("Camera Live Matrix")
        self.btn_multi.setCheckable(True)
        self.btn_multi.setStyleSheet(btn_style)
        
        self.btn_gallery = QPushButton("Incident History Log")
        self.btn_gallery.setCheckable(True)
        self.btn_gallery.setStyleSheet(btn_style)
        
        # 🟢 เพิ่มปุ่ม System Settings
        self.btn_settings = QPushButton("System Settings")
        self.btn_settings.setCheckable(True)
        self.btn_settings.setStyleSheet(btn_style)
        
        self.btn_dash.setChecked(True)
        self.btn_dash.clicked.connect(lambda: self._switch_page(0))
        self.btn_multi.clicked.connect(lambda: self._switch_page(1))
        self.btn_gallery.clicked.connect(lambda: self._switch_page(2))
        self.btn_settings.clicked.connect(lambda: self._switch_page(3)) # ผูกฟังก์ชันหน้า 4
        
        sidebar_layout.addWidget(self.btn_dash)
        sidebar_layout.addWidget(self.btn_multi)
        sidebar_layout.addWidget(self.btn_gallery)
        sidebar_layout.addWidget(self.btn_settings) # เติมเข้า Sidebar
        sidebar_layout.addStretch()
        
        layout.addWidget(sidebar)
        
        # ─────────────── PAGE WORKSPACE ───────────────
        self.pages_container = QStackedWidget()
        
        self.page_dashboard = DashboardPage()
        self.page_multicam = MultiCamPage()
        self.page_gallery = GalleryPage()
        
        self.pages_container.addWidget(self.page_dashboard)  # Index 0
        self.pages_container.addWidget(self.page_multicam)   # Index 1
        self.pages_container.addWidget(self.page_gallery)    # Index 2
        
        # 🟢 ย้ายฟังก์ชัน MultiCamPage ไปสแตนบายรอที่ Index 1 และสร้างอินสแตนซ์ให้คอมพลีท
        layout.addWidget(self.pages_container, stretch=1)

    def _switch_page(self, index):
        self.btn_dash.setChecked(index == 0)
        self.btn_multi.setChecked(index == 1)
        self.btn_gallery.setChecked(index == 2)
        self.btn_settings.setChecked(index == 3)
        self.pages_container.setCurrentIndex(index)