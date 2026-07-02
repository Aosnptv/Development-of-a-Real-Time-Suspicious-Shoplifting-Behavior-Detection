from flask import Flask, Response, jsonify, render_template_string
import cv2
from database import init_db, get_dashboard_stats
from detector import init_cameras, camera_streams
import os

app = Flask(__name__)
init_db()
init_cameras()

# สร้างหน้า Dashboard ด้วย HTML/CSS แบบรวมในไฟล์เดียว
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Operations Dashboard</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #121212; color: #ffffff; margin: 0; padding: 20px; }
        .header { border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; }
        .container { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }
        .video-grid { display: grid; grid-template-columns: 1fr; gap: 15px; }
        img.cam-feed { width: 100%; border-radius: 8px; border: 1px solid #333; }
        .panel { background-color: #1e1e1e; padding: 15px; border-radius: 8px; border: 1px solid #333; }
        .kpi-container { display: flex; justify-content: space-between; margin-bottom: 20px; }
        .kpi-card { background-color: #2a2a2a; padding: 15px; border-radius: 6px; width: 30%; text-align: center; }
        .kpi-card h3 { margin: 0; font-size: 14px; color: #aaa; }
        .kpi-card p { margin: 10px 0 0 0; font-size: 24px; font-weight: bold; color: #4caf50; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #333; }
        th { background-color: #2a2a2a; color: #aaa; }
    </style>
</head>
<body>

    <div class="header">
        <h2>Automated Shoplifting Detection (Object Tracking Core)</h2>
    </div>

    <div class="container">
        <div class="video-grid">
            <div class="panel">
                <p>Camera 1 (Main Entrance)</p>
                <img class="cam-feed" src="/video_feed/cam_1" alt="Camera 1">
            </div>
            <div class="panel">
                <p>Camera 2 (Blind Spot)</p>
                <img class="cam-feed" src="/video_feed/cam_2" alt="Camera 2">
            </div>
        </div>

        <div class="panel">
            <div class="kpi-container">
                <div class="kpi-card">
                    <h3>Total Incidents</h3>
                    <p id="total-alerts">0</p>
                </div>
                <div class="kpi-card">
                    <h3>Today's Alerts</h3>
                    <p id="today-alerts">0</p>
                </div>
                <div class="kpi-card">
                    <h3>System Status</h3>
                    <p>Online</p>
                </div>
            </div>
            
            <hr style="border-color: #333;">
            
            <h3>Recent Activity Log</h3>
            <table id="log-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Timestamp</th>
                        <th>Risk Score</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    </tbody>
            </table>
        </div>
    </div>

    <script>
        function updateStats() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('total-alerts').innerText = data.total;
                    document.getElementById('today-alerts').innerText = data.today;
                    
                    let tbody = document.querySelector('#log-table tbody');
                    tbody.innerHTML = '';
                    data.logs.forEach(log => {
                        let tr = document.createElement('tr');
                        tr.innerHTML = `<td>${log[0]}</td><td>${log[1]}</td><td>${log[2]}/5</td><td style="color:#f44336">${log[4]}</td>`;
                        tbody.appendChild(tr);
                    });
                });
        }
        
        // อัปเดตข้อมูลตารางทุกๆ 2 วินาทีโดยไม่ต้องรีเฟรชหน้า
        setInterval(updateStats, 2000);
        updateStats();
    </script>
</body>
</html>
"""

def generate_frames(cam_name):
    while True:
        if cam_name in camera_streams:
            frame = camera_streams[cam_name].read_processed()
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        else:
            time.sleep(0.1)

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/video_feed/<cam_name>')
def video_feed(cam_name):
    return Response(generate_frames(cam_name), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/stats')
def api_stats():
    total, today, logs = get_dashboard_stats()
    return jsonify({
        "total": total,
        "today": today,
        "logs": logs
    })

if __name__ == '__main__':
    # รันบน Localhost พอร์ต 5000 ปิดระบบ Debug เพื่อความเสถียร
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)