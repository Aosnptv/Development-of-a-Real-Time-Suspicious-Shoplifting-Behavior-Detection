import cv2
import os
import threading
import time
import numpy as np
from datetime import datetime
from ultralytics import YOLO
from database import log_incident

# กำหนดคลาสเป้าหมาย: 0 = Person, 39 = Bottle, 41 = Cup, 43 = Knife (อ้างอิง COCO Dataset)
TARGET_OBJECT_CLASSES = [39, 41, 43] 

CAMERA_SOURCES = {
    "cam_1": 0,
    "cam_2": 1
}

if "global_fsm_tracker" not in globals():
    global_fsm_tracker = {}

def check_overlap(box1, box2):
    """ตรวจสอบว่า Bounding Box 2 อันซ้อนทับกันหรือไม่ (Intersection)"""
    x_left = max(box1[0], box2[0])
    y_top = max(box1[1], box2[1])
    x_right = min(box1[2], box2[2])
    y_bottom = min(box1[3], box2[3])
    if x_right < x_left or y_bottom < y_top:
        return False
    return True

class ObjectFSM:
    _global_id_counter = 1
    
    def __init__(self, person_id):
        self.person_id = person_id
        self.display_id = ObjectFSM._global_id_counter
        ObjectFSM._global_id_counter += 1
        self.state = "IDLE"
        self.score = 0
        self.frames_in_state = 0
        self.is_alerted = False
        self.holding_object = False

    def update(self, person_box, objects_boxes, shelf_zone):
        if not person_box:
            return self.score

        in_shelf_zone = False
        if shelf_zone and check_overlap(person_box, shelf_zone):
            in_shelf_zone = True

        touching_object = False
        for obj_box in objects_boxes:
            if check_overlap(person_box, obj_box):
                touching_object = True
                break

        if self.state == "IDLE" and not self.is_alerted:
            if in_shelf_zone and touching_object:
                self.state = "PICKING"
                self.score = 2
                self.holding_object = True
                self.frames_in_state = 0
                
        elif self.state == "PICKING":
            if not in_shelf_zone and touching_object:
                self.state = "HOLDING"
                self.score = 3
                self.frames_in_state = 0
            elif not in_shelf_zone and not touching_object:
                # วัตถุหายไปในขณะที่เพิ่งหยิบ = อาจซุกซ่อน
                self.state = "CONCEALING"
                self.score = 4
                self.frames_in_state = 0
                
        elif self.state == "HOLDING":
            if not touching_object:
                self.state = "CONCEALING"
                self.score = 4
                self.frames_in_state = 0
            else:
                self.frames_in_state += 1
                if self.frames_in_state > 90:
                    self.score = 0
                    self.state = "IDLE"
                    
        elif self.state == "CONCEALING":
            self.frames_in_state += 1
            if self.frames_in_state > 15:
                self.state = "ALERT"
                self.score = 5
            elif touching_object:
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
        
        self.model = YOLO("yolo11n.pt")
        
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
        
        # สมมติโซนชั้นวางตายตัว (ปรับแก้พิกัดตามหน้างานจริง)
        shelf_zone = [100, 100, 400, 350]
        cv2.rectangle(frame, (shelf_zone[0], shelf_zone[1]), (shelf_zone[2], shelf_zone[3]), (255, 0, 255), 2)
        cv2.putText(frame, "SHELF ZONE", (shelf_zone[0], shelf_zone[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 255), 2)

        results = self.model.track(frame, persist=True, tracker="bytetrack.yaml", verbose=False)[0]
        
        current_persons = []
        objects_boxes = []

        if results.boxes is not None:
            for box in results.boxes:
                cls = int(box.cls[0])
                if cls in TARGET_OBJECT_CLASSES:
                    xyxy = box.xyxy[0].tolist()
                    objects_boxes.append([int(x) for x in xyxy])
                    cv2.rectangle(frame, (int(xyxy[0]), int(xyxy[1])), (int(xyxy[2]), int(xyxy[3])), (255, 165, 0), 2)

            for box in results.boxes:
                cls = int(box.cls[0])
                if cls == 0 and box.id is not None:
                    person_id = int(box.id[0])
                    tracker_key = f"{self.source}_ID_{person_id}"
                    current_persons.append(tracker_key)
                    body_box = [int(x) for x in box.xyxy[0].tolist()]

                    if tracker_key not in global_fsm_tracker:
                        global_fsm_tracker[tracker_key] = ObjectFSM(person_id)
                        
                    fsm = global_fsm_tracker[tracker_key]
                    current_score = fsm.update(body_box, objects_boxes, shelf_zone)

                    x1, y1, x2, y2 = body_box
                    if current_score == 0:
                        color = (0, 255, 0)
                    elif current_score >= 5:
                        color = (0, 0, 255)
                    else:
                        color = (0, 255, 255)
                    
                    label = f"ID:{fsm.display_id} | Risk:{current_score}/5 ({fsm.state})"
                    cv2.rectangle(frame, (x1, y1 - 25), (x1 + 220, y1), color, -1)
                    cv2.putText(frame, label, (x1 + 5, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                    if current_score >= 5 and not fsm.is_alerted:
                        fsm.is_alerted = True
                        os.makedirs("alerts", exist_ok=True)
                        img_name = f"alerts/{tracker_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                        cv2.imwrite(img_name, frame)
                        log_incident(current_score, img_name)

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