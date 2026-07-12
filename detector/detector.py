import cv2
import os
import threading
import time
import numpy as np
from datetime import datetime
from ultralytics import YOLO
from dataset.database import log_incident

# คลาสเป้าหมาย: 0=Person, 39=Bottle, 41=Cup, 43=Knife 
TARGET_CLASSES = [0, 39, 41, 43] 

# หากมีกล้องตัวเดียว ให้ใส่แค่ cam_1 เพื่อป้องกัน Error: Camera index out of range
CAMERA_SOURCES = {
    "cam_1": 0
    # "cam_2": "test_video.mp4" # (เปิดคอมเมนต์ถ้ามีวิดีโอจำลอง หรือเปลี่ยนเป็น 1 ถ้าเสียบกล้องตัวที่ 2)
}

if "global_fsm_tracker" not in globals():
    global_fsm_tracker = {}

def check_overlap(person_box, obj_box):
    """ตรวจสอบว่า Bounding Box ของวัตถุอยู่ภายในหรือทับซ้อนกับตัวคนหรือไม่"""
    px1, py1, px2, py2 = person_box
    ox1, oy1, ox2, oy2 = obj_box
    
    x_left = max(px1, ox1)
    y_top = max(py1, oy1)
    x_right = min(px2, ox2)
    y_bottom = min(py2, oy2)
    
    if x_right < x_left or y_bottom < y_top:
        return False
    return True

class AdvancedFSM:
    _global_id_counter = 1
    
    def __init__(self, person_id):
        self.person_id = person_id
        self.display_id = AdvancedFSM._global_id_counter
        AdvancedFSM._global_id_counter += 1
        self.state = "IDLE"
        self.score = 0
        self.frames_in_state = 0
        self.is_alerted = False
        
        # ตัวแปรสำหรับจดจำวัตถุที่หยิบมา
        self.held_object_id = None
        self.held_object_class = None

    def update(self, person_box, active_objects, shelf_zone):
        if not person_box:
            return self.score

        # 1. เช็คว่าคนอยู่ในโซนชั้นวางหรือไม่
        in_shelf_zone = check_overlap(person_box, shelf_zone)

        # 2. หาว่ามีวัตถุอะไรบ้างที่ซ้อนทับอยู่กับตัวคนในเฟรมนี้
        touching_objects = []
        for obj_id, (obj_box, cls) in active_objects.items():
            if check_overlap(person_box, obj_box):
                touching_objects.append((obj_id, cls))

        # 3. อัปเดตสถานะ FSM
        if self.state == "IDLE" and not self.is_alerted:
            if in_shelf_zone and touching_objects:
                self.state = "PICKING"
                self.score = 2
                # ล็อกเป้าหมาย: จดจำ ID ของวัตถุชิ้นแรกที่สัมผัส
                self.held_object_id = touching_objects[0][0]
                self.held_object_class = touching_objects[0][1]
                self.frames_in_state = 0
                
        elif self.state == "PICKING":
            # เช็คว่ายังถือ "วัตถุชิ้นเดิม" อยู่ไหม
            still_holding_target = any(obj_id == self.held_object_id for obj_id, _ in touching_objects)
            
            if not in_shelf_zone and still_holding_target:
                self.state = "HOLDING"
                self.score = 3
                self.frames_in_state = 0
            elif not in_shelf_zone and not still_holding_target:
                # เพิ่งเดินออกจากชั้นวาง แต่ของชิ้นเดิมที่ถือหายไป = ซุกซ่อน
                self.state = "CONCEALING"
                self.score = 4
                self.frames_in_state = 0
                
        elif self.state == "HOLDING":
            still_holding_target = any(obj_id == self.held_object_id for obj_id, _ in touching_objects)
            
            if not still_holding_target:
                self.state = "CONCEALING"
                self.score = 4
                self.frames_in_state = 0
            else:
                self.frames_in_state += 1
                # ถือของเดินไปมานานเกิน 3 วินาที (สมมติ 90 เฟรม) ให้ลดระดับความเสี่ยงกลับเป็นปกติ (อาจจะแค่เดินดูของ)
                if self.frames_in_state > 90:
                    self.score = 0
                    self.state = "IDLE"
                    self.held_object_id = None
                    
        elif self.state == "CONCEALING":
            self.frames_in_state += 1
            # ถ้าของหายไปครบ 15 เฟรม (มั่นใจว่าไม่ได้บั๊กกล้องกระพริบ) -> แจ้งเตือน!
            if self.frames_in_state > 15:
                self.state = "ALERT"
                self.score = 5
            else:
                # ถ้าของชิ้นเดิมโผล่กลับมา แสดงว่าแค่หลุดมุมกล้อง กลับไปสถานะ HOLDING
                still_holding_target = any(obj_id == self.held_object_id for obj_id, _ in touching_objects)
                if still_holding_target:
                    self.state = "HOLDING"
                    self.score = 3

        return self.score

class CameraStream:
    def __init__(self, source):
        self.source = source
        self.cap = cv2.VideoCapture(source)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.ret, self.frame = self.cap.read()
        self.processed_frame = self.frame.copy() if self.ret else np.zeros((480, 640, 3), dtype=np.uint8)
        self.running = True
        self.lock = threading.Lock()
        
        # อัปเกรดไปใช้ YOLOv11 รุ่น Small (ฉลาดขึ้น แม่นยำขึ้น คุ้มทรัพยากรที่สุด)
        self.model = YOLO("yolo11s.pt") 
        
        self.thread = threading.Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()

    def update(self):
        while self.running:
            if self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    frame = cv2.resize(frame, (640, 480))
                    p_frame = self.process_frame(frame)
                    with self.lock:
                        self.frame = frame
                        self.processed_frame = p_frame
                        self.ret = ret
                    time.sleep(0.03) 
                else:
                    time.sleep(0.03)

    def process_frame(self, frame):
        global global_fsm_tracker
        
        shelf_zone = [100, 100, 400, 350] # ปรับแก้พิกัดตามหน้างานจริง
        cv2.rectangle(frame, (shelf_zone[0], shelf_zone[1]), (shelf_zone[2], shelf_zone[3]), (255, 0, 255), 2)
        cv2.putText(frame, "SHELF ZONE", (shelf_zone[0], shelf_zone[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 255), 2)

        # บังคับให้ Track ทั้งคนและวัตถุไปพร้อมๆ กัน
        results = self.model.track(frame, persist=True, classes=TARGET_CLASSES, tracker="bytetrack.yaml", verbose=False)[0]
        
        current_persons = []
        active_objects = {} # เก็บ { object_id : (box_coords, class_id) }

        if results.boxes is not None:
            # 1. วนลูปเก็บข้อมูล 'วัตถุ' ทั้งหมดในเฟรมก่อน
            for box in results.boxes:
                if box.id is not None:
                    cls = int(box.cls[0])
                    if cls != 0: # ถ้าไม่ใช่มนุษย์ (แปลว่าเป็นวัตถุ)
                        obj_id = int(box.id[0])
                        xyxy = [int(x) for x in box.xyxy[0].tolist()]
                        active_objects[obj_id] = (xyxy, cls)
                        cv2.rectangle(frame, (xyxy[0], xyxy[1]), (xyxy[2], xyxy[3]), (255, 165, 0), 2)
                        cv2.putText(frame, f"Obj:{obj_id}", (xyxy[0], xyxy[1]-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,165,0), 1)

            # 2. วนลูปประมวลผลพฤติกรรม 'มนุษย์' แต่ละคน
            for box in results.boxes:
                cls = int(box.cls[0])
                if cls == 0 and box.id is not None:
                    person_id = int(box.id[0])
                    tracker_key = f"{self.source}_ID_{person_id}"
                    current_persons.append(tracker_key)
                    body_box = [int(x) for x in box.xyxy[0].tolist()]

                    if tracker_key not in global_fsm_tracker:
                        global_fsm_tracker[tracker_key] = AdvancedFSM(person_id)
                        
                    fsm = global_fsm_tracker[tracker_key]
                    
                    # ส่งพิกัดคน, ฐานข้อมูลวัตถุทั้งหมดในเฟรม, และโซนชั้นวาง ไปให้ลอจิกคิด
                    current_score = fsm.update(body_box, active_objects, shelf_zone)

                    x1, y1, x2, y2 = body_box
                    if current_score == 0:
                        color = (0, 255, 0)
                    elif current_score >= 5:
                        color = (0, 0, 255)
                    else:
                        color = (0, 255, 255)
                    
                    label = f"ID:{fsm.display_id} | Risk:{current_score}/5 ({fsm.state})"
                    
                    # เล็กน้อย: แสดง ID ของที่ถืออยู่ให้เห็นบนจอด้วย
                    if fsm.held_object_id is not None:
                        label += f" [Hold Obj:{fsm.held_object_id}]"

                    cv2.rectangle(frame, (x1, y1 - 25), (x1 + 300, y1), color, -1)
                    cv2.putText(frame, label, (x1 + 5, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                    if current_score >= 5 and not fsm.is_alerted:
                        fsm.is_alerted = True
                        os.makedirs("alerts", exist_ok=True)
                        img_name = f"alerts/{tracker_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                        cv2.imwrite(img_name, frame)
                        log_incident(current_score, img_name)

        # ล้างข้อมูลคนที่เดินออกจากกล้อง
        keys_to_delete = [k for k in global_fsm_tracker.keys() if k.startswith(str(self.source)) and k not in current_persons]
        for k in keys_to_delete:
            del global_fsm_tracker[k]

        current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cv2.putText(frame, f"TIME: {current_time_str}", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
        
        return frame

    def read_processed(self):
        with self.lock:
            return self.processed_frame.copy()

    def stop(self):
        self.running = False
        if self.cap.isOpened():
            self.cap.release()

camera_streams = {}
def init_cameras():
    for name, src in CAMERA_SOURCES.items():
        camera_streams[name] = CameraStream(src)