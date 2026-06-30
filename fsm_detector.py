import cv2
import os
import requests
import math
from datetime import datetime
from ultralytics import YOLO
from database import log_incident

# ตั้งค่า Telegram Bot (ใส่ Token และ Chat ID ของคุณที่นี่)
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"

def send_telegram_alert(image_path, score):
    """ส่งข้อความพร้อมรูปภาพหลักฐานเข้า Telegram"""
    if TELEGRAM_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        return # ข้ามการส่งถ้ายังไม่ได้ตั้งค่าโทเค็น
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    caption = f"⚠️ [แจ้งเตือนพฤติกรรมต้องสงสัย]\nเวลา: {datetime.now().strftime('%H:%M:%S')}\nคะแนนความเสี่ยง: {score} คะแนน\nกรุณาตรวจสอบหน้างาน!"
    
    try:
        with open(image_path, 'rb') as photo:
            files = {'photo': photo}
            data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption}
            requests.post(url, files=files, data=data)
    except Exception as e:
        print(f"Telegram Error: {e}")

class BehaviorFSM:
    """กลไกสถานะจำกัด (Finite State Machine) สำหรับคำนวณคะแนนความเสี่ยง"""
    def __init__(self):
        self.state = "IDLE"
        self.score = 0
        self.cooldown_frames = 0 # ป้องกันการส่งแจ้งเตือนซ้ำๆ ในทันที

    def update(self, hand_box, obj_box, body_box):
        if self.cooldown_frames > 0:
            self.cooldown_frames -= 1
            return self.score

        # ตรวจสอบการซ้อนภาพ (IoU หรือจุดศูนย์กลางใกล้กัน)
        hand_center = ((hand_box[0]+hand_box[2])/2, (hand_box[1]+hand_box[3])/2) if hand_box else None
        obj_center = ((obj_box[0]+obj_box[2])/2, (obj_box[1]+obj_box[3])/2) if obj_box else None
        
        # 1. มือสัมผัสวัตถุ (Hand touches Object) -> PICKING
        if self.state == "IDLE" and hand_center and obj_center:
            dist = math.dist(hand_center, obj_center)
            if dist < 80: # ระยะพิกเซลที่มือใกล้สินค้า
                self.state = "PICKING"
                self.score += 1

        # 2. ถือสินค้า (Holding)
        elif self.state == "PICKING":
            self.state = "HOLDING"
            
        # 3. สินค้าเข้าใกล้ลำตัว (Concealing Stage)
        elif self.state == "HOLDING" and obj_box and body_box:
            # ตรวจสอบว่าสินค้าเข้าไปในขอบเขตลำตัวหรือไม่
            if (obj_box[0] > body_box[0] and obj_box[2] < body_box[2] and
                obj_box[1] > body_box[1] and obj_box[3] < body_box[3]):
                self.state = "CONCEALING"
                self.score += 2
                
        # 4. สินค้าหายไปในบริเวณลำตัว (Concealed)
        elif self.state == "CONCEALING" and (obj_box is None) and hand_box and body_box:
            # เงื่อนไขคือมือยังอยู่ใกล้ลำตัวแต่ตัววัตถุตรวจไม่เจอแล้ว (ถูกบัง/ซ่อน)
            if hand_box[0] > body_box[0] and hand_box[2] < body_box[2]:
                self.score += 2
                self.state = "ALERT"

        # รีเซ็ตสถานะกลับมาเริ่มต้นหากพฤติกรรมหลุดวงจร
        if self.score > 0 and (hand_box is None and obj_box is None):
            self.state = "IDLE"
            self.score = max(0, self.score - 1) # ค่อยๆ ลดคะแนนลง

        return self.score

    def reset_alert(self):
        self.state = "IDLE"
        self.score = 0
        self.cooldown_frames = 100 # หยุดนับคะแนนชั่วคราวหลังแจ้งเตือนไปแล้ว

def process_video_stream():
    """ฟังก์ชันหลักในการดึงภาพจากกล้อง วิ่งโมเดล YOLO และประมวลผล FSM"""
    model = YOLO("yolo11n.pt") # โหลดโมเดล YOLOv11 อัตโนมัติ
    cap = cv2.VideoCapture(0) # 0 = กล้อง WebCam (เปลี่ยนเป็นที่อยู่ไฟล์ .mp4 หรือ RTSP IP Camera ได้)
    
    fsm = BehaviorFSM()
    os.makedirs("alerts", exist_ok=True)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # รัน YOLOv11 (สืบค้นคลาส: 0 คือ person, 43 คือ cup/object ทั่วไปตาม COCO dataset)
        # สำหรับหน้างานจริงแนะนำจับภาพคลาสกระเป๋า/ขวด/โทรศัพท์ หรือสิ่งของทั่วไป
        results = model(frame, verbose=False)[0]
        
        hand_box, obj_box, body_box = None, None, None

        for box in results.boxes:
            cls = int(box.cls[0])
            xyxy = box.xyxy[0].tolist() # [x1, y1, x2, y2]
            
            if cls == 0: # Person (ใช้แทน Body ขอบเขตลำตัว)
                body_box = xyxy
                cv2.rectangle(frame, (int(xyxy[0]), int(xyxy[1])), (int(xyxy[2]), int(xyxy[3])), (255, 0, 0), 2)
            elif cls == 43 or cls == 39: # ชิ้นส่วนวัตถุจำลอง (เช่น ถ้วย ขวด โทรศัพท์)
                obj_box = xyxy
                cv2.rectangle(frame, (int(xyxy[0]), int(xyxy[1])), (int(xyxy[2]), int(xyxy[3])), (0, 255, 0), 2)
            # หมายเหตุ: YOLO ทั่วไปจะไม่มีคลาส Hand โดยตรง หากต้องการตรวจจับเฉพาะเจาะจง 
            # ระบบจะมองว่าวัตถุชิ้นเล็กที่เคลื่อนที่เข้าหา Person คือพฤติกรรมเป้าหมาย

        # อัปเดตคะแนนผ่านระบบ FSM
        score = fsm.update(hand_box, obj_box, body_box)

        # วาดแสดงสถานะและคะแนนบนจอภาพ
        color = (0, 0, 255) if score >= 5 else (0, 255, 255)
        cv2.putText(frame, f"Risk Score: {score}/5", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)
        cv2.putText(frame, f"State: {fsm.state}", (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        # หากคะแนนถึงเกณฑ์ที่กำหนด (ตามขอบเขตงานคือ >= 5)
        if score >= 5 and fsm.state == "ALERT":
            img_name = f"alerts/alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            cv2.imwrite(img_name, frame) # เซฟภาพหลักฐาน
            log_incident(score, img_name) # บันทึกลงฐานข้อมูล SQLite
            send_telegram_alert(img_name, score)     # ส่งไลน์/โทรศัพท์ผ่าน Telegram
            fsm.reset_alert() # รีเซ็ตสถานะป้องการค้าง

        # ส่งเฟรมภาพออกไปภายนอก
        yield frame

    cap.release()