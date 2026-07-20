# services/camera_worker.py
import cv2
import numpy as np
import time
from PySide6.QtCore import QThread, Signal
from services.database_service import DatabaseService
from services.config_service import ConfigManager

class CameraWorker(QThread):
    def __init__(self, camera_id=0, video_source=0, parent=None):
        super().__init__(parent)
        self.camera_id = camera_id
        config = ConfigManager()
        
        # ดึงค่าพิกัด ROI ประจำกล้องตัวนี้มาจากไฟล์ Config ตอนเริ่มรันโปรแกรม
        self.roi_x = config.get(f"camera.cam_{camera_id + 1}_roi_x", 170)
        self.roi_y = config.get(f"camera.cam_{camera_id + 1}_roi_y", 140)
        self.roi_w = config.get(f"camera.cam_{camera_id + 1}_roi_w", 300)
        self.roi_h = config.get(f"camera.cam_{camera_id + 1}_roi_h", 200)
        
        self.product_states = {}

    def set_roi_parameters(self, x, y, w, h):
        """ฟังก์ชันสำหรับให้ UI เรียกสั่งเปลี่ยนพิกัดพื้นที่ ROI"""
        self.roi_x = max(0, min(x, 640))
        self.roi_y = max(0, min(y, 480))
        self.roi_w = max(10, min(w, 640 - self.roi_x))
        self.roi_h = max(10, min(h, 480 - self.roi_y))

    def run(self):
        cap = cv2.VideoCapture(self.video_source)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        if not cap.isOpened():
            self.frame_received.emit(self.camera_id, None)
            return

        while self.running:
            try:
                start_time = time.time()
                ret, frame = cap.read()
                
                if not ret:
                    self.frame_received.emit(self.camera_id, None)
                    time.sleep(0.03)
                    continue

                frame = cv2.resize(frame, (640, 480))

                # 🟢 คำนวณพิกัดจากค่า Setting ล่าสุด
                shelf_roi = np.array([
                    [self.roi_x, self.roi_y],
                    [self.roi_x + self.roi_w, self.roi_y],
                    [self.roi_x + self.roi_w, self.roi_y + self.roi_h],
                    [self.roi_x, self.roi_y + self.roi_h]
                ], np.int32)

                # 🟢 เพิ่มการมองเห็น (High Visibility Visualization)
                # 1. ทำแรเงาสีเขียวโปร่งแสงด้านในพื้นที่
                overlay = frame.copy()
                cv2.fillPoly(overlay, [shelf_roi], (0, 255, 0))
                cv2.addWeighted(overlay, 0.12, frame, 0.88, 0, frame)
                
                # 2. วาดเส้นขอบสีเขียวนีออนหนาขึ้น (thickness=3) ช่วยให้มองเห็นชัดเจน
                cv2.polylines(frame, [shelf_roi], isClosed=True, color=(0, 255, 0), thickness=3)
                
                # 3. เขียนข้อความกำกับพร้อมบอกพิกัดปัจจุบันบนจอภาพ
                status_txt = f"SHELF ROI [X:{self.roi_x} Y:{self.roi_y} W:{self.roi_w} H:{self.roi_h}]"
                cv2.putText(frame, status_txt, (self.roi_x, max(20, self.roi_y - 10)), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 2)

                # ลอจิกตรวจสอบวัตถุ (ดึงค่าพิกัดแบบไดนามิกมาคำนวณ)
                mock_tracked_products = [
                    {"id": 1, "box": [self.roi_x + 20, self.roi_y + 20, self.roi_x + 80, self.roi_y + 80]}
                ]

                for product in mock_tracked_products:
                    prod_id = product["id"]
                    x1, y1, x2, y2 = product["box"]
                    cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
                    
                    is_inside = cv2.pointPolygonTest(shelf_roi, (cx, cy), False) >= 0
                    
                    if prod_id not in self.product_states:
                        self.product_states[prod_id] = "NORMAL"

                    if is_inside:
                        self.product_states[prod_id] = "NORMAL"
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    else:
                        if self.product_states[prod_id] == "NORMAL":
                            self.product_states[prod_id] = "TRIGGERED"
                            self.trigger_behavior_analysis(prod_id, frame)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb_frame = np.ascontiguousarray(rgb_frame)
                self.frame_received.emit(self.camera_id, rgb_frame)
                
                elapsed_time = time.time() - start_time
                sleep_time = max(0.001, 0.033 - elapsed_time)
                time.sleep(sleep_time)

            except Exception as e:
                print(f"💥 [Camera {self.camera_id} Error]: {e}")
                time.sleep(1)

        cap.release()

    def trigger_behavior_analysis(self, product_id, current_frame):
        import os
        img_folder = "captured_alerts"
        if not os.path.exists(img_folder): os.makedirs(img_folder)
        img_path = f"{img_folder}/cam_{self.camera_id}_prod_{product_id}_{int(time.time())}.jpg"
        cv2.imwrite(img_path, current_frame)
        try:
            self.db.save_alert(camera_id=self.camera_id, image_path=img_path, details=f"Product ID {product_id} out of ROI")
        except Exception as e: print(f"❌ DB Error: {e}")

    def stop(self):
        self.running = False
        self.wait()