from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QCheckBox, QGroupBox, 
                               QFormLayout, QMessageBox, QSpinBox, QScrollArea)
from PySide6.QtCore import Qt, QSize
from services.config_service import ConfigManager

class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.is_dark_theme = True
        self.camera_inputs = {}  # เก็บวิดเจ็ตกรอกข้อมูลกล้อง { index: QLineEdit }
        
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # หัวข้อหน้า (ใช้เลขสากล)
        self.lbl_title = QLabel("⚙️ Settings (ตั้งค่าระบบ)")
        self.lbl_title.setStyleSheet("font-size: 24px; font-weight: bold;")
        main_layout.addWidget(self.lbl_title)

        # ใช้ Scroll Area เผื่อกรณีเพิ่มกล้องเยอะๆ หน้าต่างจะได้ไม่ล้น
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 0)

        # ==========================================
        # 📹 หมวดหมู่การตั้งค่ากล้อง
        # ==========================================
        self.grp_camera = QGroupBox("📹 Camera Configuration (ตั้งค่ากล้อง)")
        self.grp_camera.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.camera_form = QFormLayout(self.grp_camera)
        self.camera_form.setSpacing(15)

        # ตัวเลือกจำนวนกล้อง
        self.lbl_num_cams = QLabel("จำนวนกล้องที่ต้องการใช้งาน :")
        self.spn_num_cams = QSpinBox()
        self.spn_num_cams.setRange(1, 16)  # รองรับ 1-16 ตัว
        self.spn_num_cams.setValue(2)      
        self.spn_num_cams.setFixedWidth(80)

        self.camera_form.addRow(self.lbl_num_cams, self.spn_num_cams)
        
        # 🟢 ย้ายมาประกาศตรงนี้ก่อน เพื่อให้สร้างช่อง Dynamic ได้ถูกต้อง
        self.camera_dynamic_container = QWidget()
        self.camera_dynamic_layout = QFormLayout(self.camera_dynamic_container)
        self.camera_dynamic_layout.setContentsMargins(0, 0, 0, 0)
        self.camera_dynamic_layout.setSpacing(12)
        self.camera_form.addRow(self.camera_dynamic_container)

        # 🟢 เชื่อมต่อ Event หลังจากสร้าง Layout ข้างบนเสร็จแล้ว
        self.spn_num_cams.valueChanged.connect(self.adjust_camera_inputs)

        layout.addWidget(self.grp_camera)

        # ==========================================
        # 📱 หมวดหมู่การแจ้งเตือน Telegram
        # ==========================================
        self.grp_telegram = QGroupBox("📱 Telegram Notifications")
        self.grp_telegram.setStyleSheet("font-size: 16px; font-weight: bold;")
        telegram_layout = QFormLayout(self.grp_telegram)
        telegram_layout.setSpacing(15)

        self.chk_telegram_enabled = QCheckBox("เปิดใช้งานการแจ้งเตือนผ่าน Telegram")
        
        self.txt_bot_token = QLineEdit()
        self.txt_bot_token.setPlaceholderText("ตัวอย่าง: 123456789:ABCdefGHIjklMNOpqrSTUvwxYZ")
        
        self.txt_chat_id = QLineEdit()
        self.txt_chat_id.setPlaceholderText("ตัวอย่าง: 987654321")

        telegram_layout.addRow("", self.chk_telegram_enabled)
        telegram_layout.addRow("Bot Token :", self.txt_bot_token)
        telegram_layout.addRow("Chat ID :", self.txt_chat_id)

        layout.addWidget(self.grp_telegram)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll, stretch=1)

        # ปุ่มบันทึกการตั้งค่า
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("💾 บันทึกการตั้งค่า")
        self.btn_save.setFixedSize(180, 40)
        self.btn_save.clicked.connect(self.save_settings)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)

        main_layout.addLayout(btn_layout)
        
        # 🟢 เรียกฟังก์ชันสร้างอินพุตเริ่มต้นหลังจากสร้าง UI ครบองค์ประกอบแล้ว
        self.adjust_camera_inputs(self.spn_num_cams.value())

    def adjust_camera_inputs(self, count):
        """สร้างหรือลบช่องกรอกที่มากล้องตามจำนวนที่ผู้ใช้เลือกใน SpinBox (ใช้เลขสากล)"""
        current_count = len(self.camera_inputs)
        
        if count > current_count:
            # เพิ่มช่องกรอกข้อมูลกล้องตัวใหม่
            for i in range(current_count, count):
                txt_input = QLineEdit()
                txt_input.setPlaceholderText("ใส่เลขพอร์ต USB (เช่น 0, 1) หรือลิงก์ RTSP (rtsp://...)")
                # 🟢 เปลี่ยนมาใช้ตัวเลขปกติ (i + 1)
                self.camera_dynamic_layout.addRow(f"แหล่งที่มากล้อง {i + 1} :", txt_input)
                self.camera_inputs[i] = txt_input
        elif count < current_count:
            # ลบช่องกรอกข้อมูลกล้องส่วนเกินออก จากล่างขึ้นบน
            for i in range(current_count - 1, count - 1, -1):
                if i in self.camera_inputs:
                    self.camera_dynamic_layout.removeRow(self.camera_inputs[i])
                    del self.camera_inputs[i]
                    
        # อัปเดตสไตล์ให้เข้ากับธีมปัจจุบัน
        self.set_theme(self.is_dark_theme)

    def load_settings(self):
        """ดึงข้อมูลจาก config.json มาแสดงในหน้าต่าง"""
        self.chk_telegram_enabled.setChecked(self.config_manager.get("telegram.enabled", False))
        self.txt_bot_token.setText(self.config_manager.get("telegram.bot_token", ""))
        self.txt_chat_id.setText(self.config_manager.get("telegram.chat_id", ""))

        num_cams = self.config_manager.get("camera.num_cameras", 2)
        self.spn_num_cams.setValue(num_cams)
        self.adjust_camera_inputs(num_cams)

        for i in range(num_cams):
            cam_url = self.config_manager.get(f"camera.cam_{i + 1}", str(i))
            if i in self.camera_inputs:
                self.camera_inputs[i].setText(str(cam_url))

    def save_settings(self):
        """บันทึกข้อมูลจากหน้าต่างกลับลงไปที่ config.json"""
        if "telegram" not in self.config_manager.config:
            self.config_manager.config["telegram"] = {}
        if "camera" not in self.config_manager.config:
            self.config_manager.config["camera"] = {}
            
        self.config_manager.config["telegram"]["enabled"] = self.chk_telegram_enabled.isChecked()
        self.config_manager.config["telegram"]["bot_token"] = self.txt_bot_token.text().strip()
        self.config_manager.config["telegram"]["chat_id"] = self.txt_chat_id.text().strip()

        num_cams = self.spn_num_cams.value()
        self.config_manager.config["camera"]["num_cameras"] = num_cams
        
        # ล้างคีย์กล้องเก่าออกก่อนบันทึกใหม่
        keys_to_remove = [k for k in self.config_manager.config["camera"].keys() if k.startswith("cam_")]
        for k in keys_to_remove:
            del self.config_manager.config["camera"][k]

        for i in range(num_cams):
            if i in self.camera_inputs:
                value = self.camera_inputs[i].text().strip()
                if value.isdigit():
                    value = int(value)
                self.config_manager.config["camera"][f"cam_{i + 1}"] = value

        self.config_manager.save_config()

        msg = QMessageBox(self)
        msg.setWindowTitle("สำเร็จ")
        msg.setText("บันทึกการตั้งค่ากล้องและระบบเรียบร้อยแล้ว!\nกรุณารีสตาร์ทโปรแกรมเพื่อให้ระบบเปิดกล้องตามค่าใหม่")
        msg.setIcon(QMessageBox.Information)
        msg.exec()

    def set_theme(self, is_dark_mode):
        """จัดการสีสันเวลาสลับธีมสว่าง-มืด"""
        self.is_dark_theme = is_dark_mode
        text_color = "white" if is_dark_mode else "black"
        box_bg = "#1e293b" if is_dark_mode else "#ffffff"
        border = "#334155" if is_dark_mode else "#cbd5e1"
        input_bg = "#0f172a" if is_dark_mode else "#f8fafc"

        self.lbl_title.setStyleSheet(f"color: {text_color}; font-size: 24px; font-weight: bold;")
        
        group_style = f"""
            QGroupBox {{
                color: {text_color};
                font-size: 16px;
                font-weight: bold;
                border: 1px solid {border};
                border-radius: 8px;
                margin-top: 10px;
                background-color: {box_bg};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }}
            QLabel {{
                color: {text_color};
                font-size: 14px;
                font-weight: normal;
                background: transparent;
            }}
        """
        self.grp_telegram.setStyleSheet(group_style)
        self.grp_camera.setStyleSheet(group_style)

        input_style = f"""
            QLineEdit {{
                background-color: {input_bg};
                color: {text_color};
                border: 1px solid {border};
                border-radius: 4px;
                padding: 6px;
                font-size: 14px;
            }}
            QCheckBox {{
                color: {text_color};
                font-size: 14px;
            }}
            QSpinBox {{
                background-color: {input_bg};
                color: {text_color};
                border: 1px solid {border};
                border-radius: 4px;
                padding: 4px;
                font-size: 14px;
            }}
        """
        self.txt_bot_token.setStyleSheet(input_style)
        self.txt_chat_id.setStyleSheet(input_style)
        self.chk_telegram_enabled.setStyleSheet(input_style)
        self.spn_num_cams.setStyleSheet(input_style)
        
        for txt in self.camera_inputs.values():
            txt.setStyleSheet(input_style)

        btn_style = f"""
            QPushButton {{
                background-color: #3b82f6;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: #2563eb;
            }}
        """
        self.btn_save.setStyleSheet(btn_style)