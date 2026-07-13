from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import pyqtgraph as pg

class AnalyticsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("📊 INCIDENT ANALYTICS")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #e4e4e4; padding-bottom: 15px;")
        layout.addWidget(title)
        
        # 📈 สร้างพื้นที่วาดกราฟเส้นด้วย pyqtgraph
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground('#162447')
        self.graph_widget.setTitle("Hourly Incident Rate (Today)", color="#00adb5", size="12pt")
        self.graph_widget.setLabel('left', 'Number of Incidents', color="#a6b0cf")
        self.graph_widget.setLabel('bottom', 'Hour of Day (24h)', color="#a6b0cf")
        self.graph_widget.showGrid(x=True, y=True, alpha=0.2)
        
        # จำลองข้อมูลแกน X (เวลา) และแกน Y (จำนวนเคสที่ตรวจจับได้)
        hours = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
        incident_counts = [0, 1, 0, 4, 2, 7, 3, 1, 5, 8, 2]
        
        # วาดเส้นกราฟ
        pen = pg.mkPen(color='#00adb5', width=3)
        self.graph_widget.plot(hours, incident_counts, pen=pen, symbol='o', symbolSize=8, symbolBrush='#ffffff')
        
        layout.addWidget(self.graph_widget)