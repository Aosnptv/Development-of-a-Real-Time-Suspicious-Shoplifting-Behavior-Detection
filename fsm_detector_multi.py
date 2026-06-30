import cv2
import os
import requests
import math
import threading
from datetime import datetime
from ultralytics import YOLO
from database import log_incident

CAMERA_SOURCES = {
    "กล้องที่ 1 (หน้าร้าน)": 0,
    "กล้องที่ 2 (ชั้นวางสินค้า)": 1
}

TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"

if "global_fsm_tracker" not in globals():
    global_fsm_tracker = {}

def send_telegram_alert(image_path, person_id, score):
    if TELEGRAM_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    caption = f"⚠️ [แจ้งเตือนพฤติกรรมต้องสงสัย]\nID บุคคล: {person_id}\nคะแนนความเสี่ยง: {score}/5 คะแนน\nกรุณาตรวจสอบด่วน!"
    try:
        with open(image_path, 'rb') as photo:
            requests.post(url, files={'photo': photo}, data={'chat_id': TELEGRAM_CHAT_ID, 'caption': caption})
    except Exception as e:
        print(f"Telegram Error: {e}")

class IndividualFSM:
    def __init__(self, person_id):
        self.person_id = person_id
        self.state = "IDLE"
        self.score = 0
        self.frames_in_state = 0
        self.is_alerted = False

    def update(self, left_hand, right_hand, body_box, zone_coords):
        if not body_box or zone_coords is None:
            return self.score

        bx1, by1, bx2, by2 = body_box
        body_width = bx2 - bx1
        body_height = by2 - by1

        # เช็กพิกัดมือเข้าโซน
        hand_in_product_zone = False
        for hand in [left_hand, right_hand]:
            if hand:
                hx, hy = hand
                if (zone_coords[0] < hx < zone_coords[2]) and (zone_coords[1] < hy < zone_coords[3]):
                    hand_in_product_zone = True

        # เช็กพิกัดมือเข้าลำตัว
        hand_in_body_area = False
        for hand in [left_hand, right_hand]:
            if hand:
                hx, hy = hand
                if (bx1 < hx < bx2) and (by1 + (body_height * 0.25) < hy < by1 + (body_height * 0.85)):
                    hand_in_body_area = True

        # FSM Logic
        if self.state == "IDLE" and not self.is_alerted:
            if hand_in_product_zone:
                self.state = "PICKING"
                self.score = 1
                self.frames_in_state = 0

        elif self.state == "PICKING":
            if not hand_in_product_zone: 
                self.state = "HOLDING"
                self.score = 2
                self.frames_in_state = 0

        elif self.state == "HOLDING":
            if hand_in_body_area:
                self.state = "CONCEALING"
                self.score = 4
                self.frames_in_state = 0
            else:
                self.frames_in_state += 1
                if self.frames_in_state > 60: 
                    self.score = 0
                    self.state = "IDLE"

        elif self.state == "CONCEALING":
            self.frames_in_state += 1
            if hand_in_body_area and self.frames_in_state > 10:
                self.state = "ALERT"
                self.score = 5
            elif not hand_in_body_area:
                self.state = "HOLDING"
                self.score = 2

        return self.score

class CameraStream:
    def __init__(self, source):
        self.cap = cv2.VideoCapture(source)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.ret, self.frame = self.cap.read()
        self.running = True
        self.lock = threading.Lock() # เพิ่ม Lock ป้องกันภาพพังเวลาดึงข้อมูลข้าม Thread
        self.thread = threading.Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()

    def update(self):
        while self.running:
            if self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    with self.lock:
                        self.frame = cv2.resize(frame, (640, 480))
                        self.ret = ret

    def read(self):
        with self.lock:
            return self.ret, self.frame if self.frame is not None else None

    def stop(self):
        self.running = False
        self.cap.release()

# โหลดโมเดล Pose ไว้ล่วงหน้า
pose_model = YOLO("yolo11n-pose.pt")

def process_frame_pipeline(frame, camera_name, zone_coords):
    global global_fsm_tracker
    if frame is None or zone_coords is None:
        return frame
        
    # วาดกรอบ PRODUCT ZONE สีม่วง
    cv2.rectangle(frame, (zone_coords[0], zone_coords[1]), (zone_coords[2], zone_coords[3]), (255, 0, 255), 2)
    cv2.putText(frame, f"PRODUCT ZONE ({camera_name})", (zone_coords[0], zone_coords[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)

    # รันโมเดลตรวจจับท่าทางบุคคล
    pose_results = pose_model.track(frame, persist=True, tracker="bytetrack.yaml", verbose=False)[0]
    current_frame_ids = []

    if pose_results.boxes is not None and pose_results.keypoints is not None:
        for idx, box in enumerate(pose_results.boxes):
            if box.id is None:
                continue
            
            cls = int(box.cls[0])
            if cls == 0:  
                person_id = int(box.id[0])
                tracker_key = f"{camera_name}_ID_{person_id}"
                current_frame_ids.append(tracker_key)
                body_box = box.xyxy[0].tolist()

                if tracker_key not in global_fsm_tracker:
                    global_fsm_tracker[tracker_key] = IndividualFSM(person_id)

                keypoints = pose_results.keypoints[idx].xy[0].tolist()
                left_hand, right_hand = None, None
                
                if len(keypoints) > 10:
                    if keypoints[9][0] > 0 and keypoints[9][1] > 0:
                        left_hand = (keypoints[9][0], keypoints[9][1])
                        cv2.circle(frame, (int(left_hand[0]), int(left_hand[1])), 8, (255, 255, 0), -1)
                    if keypoints[10][0] > 0 and keypoints[10][1] > 0:
                        right_hand = (keypoints[10][0], keypoints[10][1])
                        cv2.circle(frame, (int(right_hand[0]), int(right_hand[1])), 8, (255, 255, 0), -1)

                current_score = global_fsm_tracker[tracker_key].update(left_hand, right_hand, body_box, zone_coords)
                current_state = global_fsm_tracker[tracker_key].state

                x1, y1, x2, y2 = map(int, body_box)
                color = (0, 0, 255) if current_score >= 5 else (0, 255, 255)
                
                label = f"ID: {person_id} | Risk: {current_score}/5 ({current_state})"
                cv2.rectangle(frame, (x1, y1 - 35), (x1 + 240, y1), color, -1)
                cv2.putText(frame, label, (x1 + 5, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                if current_score >= 5 and not global_fsm_tracker[tracker_key].is_alerted:
                    global_fsm_tracker[tracker_key].is_alerted = True
                    os.makedirs("alerts", exist_ok=True)
                    img_name = f"alerts/{tracker_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                    cv2.imwrite(img_name, frame)
                    log_incident(current_score, img_name)
                    send_telegram_alert(img_name, person_id, current_score)

    for key in list(global_fsm_tracker.keys()):
        if key.startswith(camera_name) and key not in current_frame_ids:
            del global_fsm_tracker[key]

    return frame