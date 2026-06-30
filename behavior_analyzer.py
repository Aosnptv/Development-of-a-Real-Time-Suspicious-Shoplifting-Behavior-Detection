# behavior_analyzer.py
import math
import time
import numpy as np

class BehaviorAnalyzer:
    def __init__(self):
        # โครงสร้างจัดเก็บสถานะอ้างอิงด้วย Global Key (ชื่อบุคคล) แทน Tracking ID รายกล้อง
        self.global_person_states = {}

    def _init_person_if_not_exists(self, person_key):
        if person_key not in self.global_person_states:
            self.global_person_states[person_key] = {
                "state": "Idle",
                "suspicion_score": 0,
                "history": [],
                "last_seen_box": None
            }

    def update_behavior(self, person_key, person_box, hand_boxes, object_boxes):
        """ ประเมินสเตตัสพฤติกรรมการสัมผัสและซ่อนสินค้าโดยสะสมคะแนนต่อเนื่องไม่ว่าจะจับภาพได้จากกล้องมุมใดก็ตาม """
        self._init_person_if_not_exists(person_key)
        user_data = self.global_person_states[person_key]
        user_data["last_seen_box"] = person_box
        
        px1, py1, px2, py2 = person_box
        p_center = np.array([(px1 + px2) / 2, (py1 + py2) / 2])
        
        hand_near_object = False
        object_near_body = False
        
        # ตรวจสอบความสัมพันธ์เชิงพื้นที่ระยะพิกเซลในการสัมผัส (Spatial Relationship)
        for h_box in hand_boxes:
            hx1, hy1, hx2, hy2 = h_box
            h_center = np.array([(hx1 + hx2) / 2, (hy1 + hy2) / 2])
            for o_box in object_boxes:
                ox1, oy1, ox2, oy2 = o_box
                o_center = np.array([(ox1 + ox2) / 2, (oy1 + oy2) / 2])
                
                # ตรวจสอบมือใกล้ชิ้นสินค้า
                if np.linalg.norm(h_center - o_center) < 50:
                    hand_near_object = True
                    
                # ตรวจสอบวัตถุเข้าใกล้พิกัดลำตัวบุคคล
                if np.linalg.norm(o_center - p_center) < 70:
                    object_near_body = True

        # ลำดับกลไกการเปลี่ยนสถานะ FSM และเงื่อนไขถ่วงน้ำหนักค่านะคะแนน (Weight) ตามข้อกำหนดโครงการ
        current_state = user_data["state"]
        
        if current_state == "Idle" and hand_near_object:
            user_data["state"] = "Picking"
            user_data["suspicion_score"] += 1  # มือสัมผัสสินค้า = +1
            user_data["history"].append("Picking")
            
        elif current_state == "Picking" and object_near_body:
            user_data["state"] = "Holding"
            user_data["suspicion_score"] += 2  # สินค้าเข้าใกล้ลำตัว = +2
            user_data["history"].append("Holding")
            
        elif current_state == "Holding" and not hand_near_object and object_near_body:
            # วัตถุถูกบดบังหรือหายไปในตำแหน่งบริเวณแนวลำตัว
            user_data["state"] = "Concealing"
            user_data["suspicion_score"] += 3  # สินค้าหายจากเฟรมบริเวณลำตัว = +3
            user_data["history"].append("Concealing")
            
        return user_data["state"], user_data["suspicion_score"]

class BehaviorAnalyzer:
    def __init__(self):
        # ออกแบบโครงสร้าง FSM เก็บค่าสถานะและคะแนนสะสมแยกอิสระต่อกล้องแต่ละตัว
        # State: 0=Idle, 1=Picking, 2=Holding, 3=Concealing
        self.camera_states = {
            "CAM 01": {"state": 0, "score": 0, "last_action_time": time.time()},
            "CAM 02": {"state": 0, "score": 0, "last_action_time": time.time()},
            "CAM 03": {"state": 0, "score": 0, "last_action_time": time.time()},
            "CAM 04": {"state": 0, "score": 0, "last_action_time": time.time()},
        }
        
    def calculate_distance(self, p1, p2):
        """คำนวณระยะทางแบบยูคลิเดียน (Euclidean Distance) ระหว่างจุดพิกัดในภาพ"""
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

    def analyze_pose_and_objects(self, cam_id, pose_results, object_results):
        """
        วิเคราะห์ท่าทางสัดส่วนร่างกายร่วมกับตำแหน่งวัตถุ เพื่อเปลี่ยนสถานะ FSM และคำนวณคะแนน (+/-)
        """
        current_time = time.time()
        cam = self.camera_states[cam_id]
        
        # 1. ดึงตำแหน่งพิกัดจุดศูนย์กลางของวัตถุ/สินค้าจำลองในเฟรม (เช่น บรรจุภัณฑ์ ขวด หรือกระเป๋า)
        object_centers = []
        if len(object_results) > 0 and object_results[0].boxes is not None:
            for box in object_results[0].boxes:
                class_id = int(box.cls[0])
                label = object_results[0].names[class_id]
                # ในที่นี้กำหนดคลาสมาตรฐาน COCO ให้เป็นตัวแทนสินค้าในการทดสอบ
                if label in ["bottle", "cup", "cell phone", "backpack", "handbag"]:
                    xyxy = box.xyxy[0].tolist()
                    xc = (xyxy[0] + xyxy[2]) / 2
                    yc = (xyxy[1] + xyxy[3]) / 2
                    object_centers.append((xc, yc))

        # 2. ตรวจสอบพิกัดสัดส่วนโครงกระดูกร่างกาย (Keypoints จาก Pose Model)
        has_person = False
        hand_near_product = False
        product_near_torso = False
        product_disappeared = False

        if len(pose_results) > 0 and pose_results[0].keypoints is not None:
            keypoints_data = pose_results[0].keypoints.xy # พิกัดตำแหน่งบนจอภาพ (N, 17, 2)
            if len(keypoints_data) > 0 and len(keypoints_data[0]) > 12:
                has_person = True
                kp = keypoints_data[0].tolist() # นำข้อมูลบุคคลหลักคนแรกมาทำการวิเคราะห์
                
                # ดึงจุดข้อมือซ้าย (9) และข้อมือขวา (10) เพื่อใช้แทนพิกัด "มือ"
                left_wrist = kp[9]
                right_wrist = kp[10]
                
                # คำนวณจุดกึ่งกลางลำตัว (Torso Center) จาก ไหล่ซ้าย/ขวา (5,6) และสะโพกซ้าย/ขวา (11,12)
                torso_x = (kp[5][0] + kp[6][0] + kp[11][0] + kp[12][0]) / 4
                torso_y = (kp[5][1] + kp[6][1] + kp[11][1] + kp[12][1]) / 4
                torso_center = (torso_x, torso_y)

                # ตรวจสอบความสัมพันธ์เชิงพื้นที่ (Spatial Relationship)
                for obj_pos in object_centers:
                    # ตรวจสอบว่ามือเข้าใกล้สินค้าหรือไม่ (รัศมี 60 พิกเซล)
                    if (self.calculate_distance(left_wrist, obj_pos) < 60 and left_wrist != [0,0]) or \
                       (self.calculate_distance(right_wrist, obj_pos) < 60 and right_wrist != [0,0]):
                        hand_near_product = True
                    
                    # ตรวจสอบว่าสินค้าย้ายเข้ามาใกล้ลำตัวหรือไม่ (รัศมี 80 พิกเซล)
                    if self.calculate_distance(torso_center, obj_pos) < 80 and torso_center != (0,0):
                        product_near_torso = True

                # ตรวจสอบเงื่อนไขสินค้าหายไปบริเวณลำตัว (หากก่อนหน้านี้ถืออยู่ แล้วจู่ๆ สินค้าในเฟรมหายไป)
                if cam["state"] == 2 and len(object_centers) == 0:
                    product_disappeared = True

        # 3. กลไก Logic การเปลี่ยนสถานะสถานะ (FSM) และการคิดคะแนนสะสม (+ / -)
        new_log = None
        
        # กรณีไม่มีคนอยู่บนหน้าจอเลย: ทำการ Decay สลายคะแนนลงเพื่อความเสถียร (-)
        if not has_person:
            if current_time - cam["last_action_time"] > 2.0:
                cam["score"] = max(0, cam["score"] - 1)
                if cam["score"] == 0:
                    cam["state"] = 0
                cam["last_action_time"] = current_time
        else:
            # ลำดับการก้าวขึ้นของสถานะ (State Step-up)
            if cam["state"] == 0 and hand_near_product:
                cam["state"] = 1 # ย้ายไปขั้นตอนหยิบจับ
                cam["score"] += 1 # สัมผัสสินค้า = +1 คะแนน
                cam["last_action_time"] = current_time
                new_log = f"[{cam_id}] พฤติกรรม: Picking - มีการยื่นมือจับวัตถุ (+1)"
                
            elif cam["state"] == 1:
                if product_near_torso:
                    cam["state"] = 2 # ย้ายไปสถานะถือประคองใกล้ตัว
                    cam["score"] += 2 # สินค้าใกล้ลำตัว = +2 คะแนน
                    cam["last_action_time"] = current_time
                    new_log = f"[{cam_id}] พฤติกรรม: Holding - นำวัตถุเข้ามาใกล้บริเวณลำตัว (+2)"
                # กลไกติดลบ (-): หากหยิบค้างไว้เฉยๆ นานเกิน 5 วินาทีแล้วไม่มีพฤติกรรมแย่ลง ให้ลดสถานะคืน
                elif current_time - cam["last_action_time"] > 5.0:
                    cam["state"] = 0
                    cam["score"] = max(0, cam["score"] - 1)
                    cam["last_action_time"] = current_time
                    
            elif cam["state"] == 2:
                if product_disappeared:
                    cam["state"] = 3 # ย้ายไปสถานะวิกฤต (ซ่อนสินค้า)
                    cam["score"] += 2 # สินค้าหายไปจุดอับลำตัว = คะแนนเต็มลิมิต (+2) รวมเป็น 5 คะแนน
                    cam["last_action_time"] = current_time
                    new_log = f"[{cam_id}] ALERT: Concealing - วัตถุสูญหายไปในบริเวณลำตัวบุคคล (+2)"
                # กลไกติดลบ (-): หากลูกค้านำสินค้าออกห่างลำตัว (เช่น วางคืนชั้น) เกิน 4 วินาที ให้ลดคะแนนความเสี่ยงลง
                elif not product_near_torso:
                    if current_time - cam["last_action_time"] > 4.0:
                        cam["state"] = 1
                        cam["score"] = max(0, cam["score"] - 2)
                        cam["last_action_time"] = current_time
                        new_log = f"[{cam_id}] ลดคะแนนความเสี่ยง วัตถุถูกนำออกห่างจากลำตัว (-2)"

            elif cam["state"] == 3:
                # เคลียร์สถานะอันตรายกลับสู่ปกติหลังจากผ่านไป 10 วินาที เพื่อรีเซ็ตระบบเฝ้าระวังใหม่
                if current_time - cam["last_action_time"] > 10.0:
                    cam["state"] = 0
                    cam["score"] = 0
                    cam["last_action_time"] = current_time
                    new_log = f"[{cam_id}] ระบบคูลดาวน์ รีเซ็ตสถานะมอนิเตอร์กลับสู่ค่าเริ่มต้น"

        # ควบคุมคะแนนให้อยู่ในช่วงขอบเขตที่กำหนด (0 ถึง 5 คะแนน)
        cam["score"] = max(0, min(5, cam["score"]))
        self.camera_states[cam_id] = cam
        
        return cam["score"], cam["state"], new_log