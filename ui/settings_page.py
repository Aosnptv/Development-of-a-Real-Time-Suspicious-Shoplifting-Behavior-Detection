from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QGroupBox
from PySide6.QtCore import Qt

class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        self.title = QLabel("⚙️ Telegram Notifications Settings")
        layout.addWidget(self.title)
        
        self.group_box = QGroupBox("Bot Configuration")
        form_layout = QVBoxLayout(self.group_box)
        form_layout.setContentsMargins(20, 25, 20, 20)
        form_layout.setSpacing(10)
        
        self.lbl_token = QLabel("Telegram Bot Token:")
        self.input_token = QLineEdit()
        self.input_token.setPlaceholderText("Enter your bot token...")
        self.input_token.setMaximumWidth(450)
        
        self.lbl_chatid = QLabel("Target Chat ID:")
        self.input_chatid = QLineEdit()
        self.input_chatid.setPlaceholderText("Enter target chat ID...")
        self.input_chatid.setMaximumWidth(450)
        
        self.btn_save = QPushButton("💾 Save Configuration")
        self.btn_save.setMaximumWidth(160)
        
        form_layout.addWidget(self.lbl_token)
        form_layout.addWidget(self.input_token)
        form_layout.addSpacing(10)
        form_layout.addWidget(self.lbl_chatid)
        form_layout.addWidget(self.input_chatid)
        form_layout.addSpacing(15)
        form_layout.addWidget(self.btn_save)
        
        layout.addWidget(self.group_box)

    def set_theme(self, is_dark_mode):
        fg = "white" if is_dark_mode else "black"
        bg_card = "#1e293b" if is_dark_mode else "#ffffff"
        border = "#334155" if is_dark_mode else "#cbd5e1"
        
        self.title.setStyleSheet(f"color: {fg}; font-size: 20px; font-weight: bold;")
        self.group_box.setStyleSheet(f"QGroupBox {{ color: #38bdf8; font-weight: bold; border: 1px solid {border}; border-radius: 6px; margin-top: 10px; background-color: {bg_card}; }} QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 5px; }}")
        
        self.lbl_token.setStyleSheet(f"color: {fg}; font-weight: bold;")
        self.lbl_chatid.setStyleSheet(f"color: {fg}; font-weight: bold;")
        
        input_style = f"background-color: {'#0f172a' if is_dark_mode else '#f1f5f9'}; color: {fg}; padding: 8px; border: 1px solid {border}; border-radius: 4px;"
        self.input_token.setStyleSheet(input_style)
        self.input_chatid.setStyleSheet(input_style)
        
        self.btn_save.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; padding: 10px; border-radius: 4px;")