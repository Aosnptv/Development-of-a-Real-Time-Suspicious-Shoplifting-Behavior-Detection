from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider, QLineEdit, QPushButton, QFormLayout, QGroupBox, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from core.app_state import AppState
from services.logger import logger

class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.state = AppState() # เข้าถึงจุดเก็บสถานะกลางของแอป
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        title = QLabel("⚙️ SYSTEM SETTINGS")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #e4e4e4;")
        layout.addWidget(title)
        
        # 🟢 ดึงค่าแบบปลอดภัย: ตรวจสอบก่อนว่ามี attribute หรือ config dict หรือไม่
        # ถ้าไม่มี ให้ Fallback ไปค่า Default (0.50, ว่าง, ว่าง)
        if hasattr(self.state, "config") and isinstance(self.state.config, dict):
            raw_thresh = self.state.config.get("model_threshold", 0.50)
            token_val = self.state.config.get("telegram_token", "")
            chat_val = self.state.config.get("telegram_chat_id", "")
        else:
            # ดึงตรง ๆ จาก attribute เผื่อโครงสร้างเดิมของคุณประกาศแยกไว้
            raw_thresh = getattr(self.state, "model_threshold", 0.50)
            token_val = getattr(self.state, "telegram_token", "")
            chat_val = getattr(self.state, "telegram_chat_id", "")

        current_thresh = int(raw_thresh * 100)
        
        # --- โซนปรับแต่งโมเดล ---
        ai_group = QGroupBox("AI Detector Parameters")
        ai_group.setStyleSheet("QGroupBox { color: #00adb5; font-weight: bold; border: 1px solid #1f4068; border-radius: 6px; margin-top: 10px; padding-top: 15px; }")
        ai_form = QFormLayout(ai_group)
        
        self.lbl_thresh = QLabel(f"Confidence Threshold ({current_thresh / 100:.2f})")
        self.lbl_thresh.setStyleSheet("color: #e4e4e4;")
        
        self.slider_thresh = QSlider(Qt.Orientation.Horizontal)
        self.slider_thresh.setRange(10, 100)
        self.slider_thresh.setValue(current_thresh)
        self.slider_thresh.valueChanged.connect(self._on_slider_changed)
        ai_form.addRow(self.lbl_thresh, self.slider_thresh)
        layout.addWidget(ai_group)
        
        # --- โซนตั้งค่าการแจ้งเตือน Telegram ---
        alert_group = QGroupBox("Telegram Notification API")
        alert_group.setStyleSheet("QGroupBox { color: #00adb5; font-weight: bold; border: 1px solid #1f4068; border-radius: 6px; margin-top: 10px; padding-top: 15px; }")
        alert_form = QFormLayout(alert_group)
        
        self.txt_bot_token = QLineEdit()
        self.txt_bot_token.setText(str(token_val))
        self.txt_bot_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_bot_token.setStyleSheet("background-color: #162447; color: white; border: 1px solid #1f4068; padding: 4px;")
        
        self.txt_chat_id = QLineEdit()
        self.txt_chat_id.setText(str(chat_val))
        self.txt_chat_id.setStyleSheet("background-color: #162447; color: white; border: 1px solid #1f4068; padding: 4px;")
        
        alert_form.addRow(QLabel("Bot Token:"), self.txt_bot_token)
        alert_form.addRow(QLabel("Chat ID:"), self.txt_chat_id)
        
        for i in range(alert_form.count()):
            w = alert_form.itemAt(i).widget()
            if isinstance(w, QLabel): 
                w.setStyleSheet("color: #e4e4e4;")
        layout.addWidget(alert_group)
        
        # ปุ่มเซฟบันทึกค่าคอนฟิก
        btn_save = QPushButton("💾 Save Preferences")
        btn_save.setStyleSheet("background-color: #00adb5; color: white; font-weight: bold; padding: 8px; border: none; border-radius: 4px;")
        btn_save.clicked.connect(self._save_settings)
        layout.addWidget(btn_save)
        layout.addStretch()
        
    def _on_slider_changed(self, val):
        self.lbl_thresh.setText(f"Confidence Threshold ({val / 100:.2f})")
        
    def _save_settings(self):
        """นำค่าบน GUI ไปเขียนบันทึกกลับเข้าสเตตัสกลางแบบปลอดภัย"""
        # 🟢 แก้ไขจุดพิมพ์ผิดจาก .setValue() เป็น .value() เพื่อดึงค่าสไลด์เดอร์
        new_thresh = self.slider_thresh.value() / 100.0
        bot_token = self.txt_bot_token.text().strip()
        chat_id = self.txt_chat_id.text().strip()
        
        # บันทึกค่ากลับลง AppState โดยรองรับทั้งแบบ dict และแบบอัปเดต attribute ตรง ๆ
        if hasattr(self.state, "config") and isinstance(self.state.config, dict):
            self.state.config["model_threshold"] = new_thresh
            self.state.config["telegram_token"] = bot_token
            self.state.config["telegram_chat_id"] = chat_id
        else:
            # อัปเดตผูกเข้าตัวแปรคลาสตรง ๆ
            self.state.model_threshold = new_thresh
            self.state.telegram_token = bot_token
            self.state.telegram_chat_id = chat_id
        
        logger.info(f"[Config] System parameters updated: Thresh={new_thresh}")
        QMessageBox.information(self, "Success", "System configuration saved and synced with AI Engine.")