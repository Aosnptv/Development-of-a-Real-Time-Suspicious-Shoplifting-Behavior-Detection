import cv2
import os
import requests
import math
from datetime import datetime
from ultralytics import YOLO
from database import log_incident

# ----------------- CONFIGURATION -----------------
# ระบุไอดีกล้อง หรือที่อยู่ IP Camera (เช่น "rtsp://admin:12345@192.168.1.50:554/stream1")
CAMERA_SOURCES = [0]  # [0, 1] หากต้องการต่อเว็บแคม 2 ตัวพร้อมกัน

TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"
# -------------------------------------------------

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
    """ระบบ FSM สำหรับคำนวณคะแนนแยกรายบุคคลตาม ID"""
    def __init__(self, person_id):
        self.person_id = person_id
        self.state = "IDLE"
        self.score = 0
        self.cooldown = 0

    def update(self, hand_box, obj_box, body_box):
        if self.cooldown > 0:
            self.cooldown -= 1
            return self.score

        hand_center = ((hand_box[0]+hand_box[2])/2, (hand_box[1]+hand_box[3])/2) if hand_box else None
        obj_center = ((obj_box[0]+obj_box[2])/2, (obj_box[1]+obj_box[3])/2) if obj_box else None
        
        # FSM Sequential Logic
        if self.state == "IDLE" and hand_center and obj_center:
            if math.dist(hand_center, obj_center) < 70:
                self.state = "PICKING"
                self.score += 1

        elif self.state == "PICKING":
            self.state = "HOLDING"
            
        elif self.state == "HOLDING" and obj_box and body_box:
            if (obj_box[0] > body_box[0] and obj_box[2] < body_box[2] and
                obj_box[1] > body_box[1] and obj_box[3] < body_box[3]):
                self.state = "CONCEALING"
                self.score += 2
                
        elif self.state == "CONCEALING" and (obj_box is None) and hand_box and body_box:
            if hand_box[0] > body_box[0] and hand_box[2] < body_box[2]:
                self.score += 2
                self.state = "ALERT"

        if self.score > 0 and hand_box is None and obj_box is None:
            self.state = "IDLE"
            self.score = max(0, self.score - 1)

        return self.score

    def reset(self):
        self.state = "IDLE"
        self.score = 0
        self.cooldown = 150 # หยุดจับตาคนนี้สักพักหลังแจ้งเตือนไปแล้ว

def process_multi_camera(camera_index=0):
    """ฟังก์ชันเปิดกล้องแต่ละตัว ทำ Tracking ระบุ ID และคำนวณคะแนนบนหัว"""
    model = YOLO("yolo11n.pt")
    cap = cv2.VideoCapture(camera_index)
    
    # ดิกชันนารีเก็บคลาส FSM แยกตามตัวบุคคล {person_id: IndividualFSM_Object}
    tracked_persons = {}
    os.makedirs("alerts", exist_ok=True)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # เรียกใช้โมเดลพร้อมเปิดระบบ Tracking (ByteTrack)
        results = model.track(frame, persist=True, tracker="bytetrack.yaml", verbose=False)[0]
        
        # วิ่งหาออบเจกต์รอบข้างก่อน (มือ/สินค้า) เพื่อเอาไปเทียบกับตัวบุคคล
        hands, objects = [], []
        for box in results.boxes:
            cls = int(box.cls[0])
            xyxy = box.xyxy[0].tolist()
            if cls == 43 or cls == 39:  # คลาสสินค้า/วัตถุจำลอง
                objects.append(xyxy)
                cv2.rectangle(frame, (int(xyxy[0]), int(xyxy[1])), (int(xyxy[2]), int(xyxy[3])), (0, 255, 0), 1)

        # วนลูปประมวลผลเฉพาะ "คน" ที่ถูกระบุ ID
        for box in results.boxes:
            if box.id is None:
                continue
            
            cls = int(box.cls[0])
            if cls == 0:  # เจอคน (Person)
                person_id = int(box.id[0]) # ดึง ID คนที่ 1, 2, 3...
                body_box = box.xyxy[0].tolist()

                # สร้างตัวนับคะแนนใหม่หากเป็นบุคคลใหม่ที่เพิ่งเดินเข้ากล้อง
                if person_id not in tracked_persons:
                    tracked_persons[person_id] = IndividualFSM(person_id)

                # ค้นหามือและวัตถุที่อยู่ใกล้หรือสัมพันธ์กับบุคคล ID นี้
                my_hand = None
                my_obj = None
                
                # มองหาวัตถุที่อยู่ในรัศมีขอบเขตตัวของ ID นี้
                for obj in objects:
                    if (obj[0] > body_box[0] - 20 and obj[2] < body_box[2] + 20):
                        my_obj = obj
                        break

                # อัปเดตสถานะ FSM และคะแนนของคนคนนี้
                current_score = tracked_persons[person_id].update(my_hand, my_obj, body_box)
                current_state = tracked_persons[person_id].state

                # วาดกรอบและ "แสดงไอดีพร้อมคะแนนบนหัว"
                x1, y1, x2, y2 = map(int, body_box)
                color = (0, 0, 255) if current_score >= 5 else (0, 255, 255)
                
                # วาดป้ายบนหัวบุคคล
                label = f"ID: {person_id} | Score: {current_score}/5 ({current_state})"
                cv2.rectangle(frame, (x1, y1 - 30), (x1 + 320, y1), color, -1)
                cv2.putText(frame, label, (x1 + 5, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                # เงื่อนไขแจ้งเตือนภัย
                if current_score >= 5 and current_state == "ALERT":
                    img_name = f"alerts/cam{camera_index}_id{person_id}_{datetime.now().strftime('%M%S')}.jpg"
                    cv2.imwrite(img_name, frame)
                    log_incident(current_score, img_name)
                    send_telegram_alert(img_name, person_id, current_score)
                    tracked_persons[person_id].reset()

        yield frame

    cap.release()