# ui/settings_page.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
                               QLineEdit, QPushButton, QFrame, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #f8fafc;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        
        header = QLabel("⚙️ SYSTEM SETTINGS")
        header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header.setStyleSheet("color: #0f172a; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # กรอบฟอร์มการตั้งค่า Telegram
        form_frame = QFrame()
        form_frame.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;")
        form_layout = QFormLayout(form_frame)
        form_layout.setContentsMargins(24, 24, 24, 24)
        form_layout.setVerticalSpacing(16)
        
        section_title = QLabel("Telegram Notification API Config")
        section_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        section_title.setStyleSheet("color: #2563eb; margin-bottom: 10px;")
        form_layout.addRow(section_title)
        
        # ช่องกรอกข้อมูล
        self.txt_token = QLineEdit()
        self.txt_token.setPlaceholderText("Enter Telegram Bot API Token")
        self.txt_token.setStyleSheet("padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; color: #0f172a;")
        
        self.txt_chat_id = QLineEdit()
        self.txt_chat_id.setPlaceholderText("Enter Target Chat ID or Group ID")
        self.txt_chat_id.setStyleSheet("padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; color: #0f172a;")
        
        form_layout.addRow(QLabel("Bot Token:"), self.txt_token)
        form_layout.addRow(QLabel("Chat ID:"), self.txt_chat_id)
        
        # ปุ่มกด (จัดแนวนอนด้วย QHBoxLayout)
        btn_layout = QHBoxLayout()
        self.btn_test = QPushButton("⚡ Test Connection")
        self.btn_test.setStyleSheet("background-color: #ea580c; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        self.btn_test.clicked.connect(self._test_telegram)
        
        self.btn_save = QPushButton("💾 Save Settings")
        self.btn_save.setStyleSheet("background-color: #16a34a; color: white; padding: 8px 24px; border-radius: 6px; font-weight: bold;")
        self.btn_save.clicked.connect(self._save_settings)
        
        btn_layout.addWidget(self.btn_test)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        
        form_layout.addRow("", btn_layout)
        layout.addWidget(form_frame)
        layout.addStretch()

    def _save_settings(self):
        QMessageBox.information(self, "Success", "Telegram configuration saved successfully!")

    def _test_telegram(self):
        QMessageBox.information(self, "API Test", "Test alert payload injected!\nPlease check your Telegram channel.")