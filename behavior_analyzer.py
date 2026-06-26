# behavior_analyzer.py
import time

class BehaviorAnalyzer:
    def __init__(self, max_score=5):
        self.max_score = max_score
        # เก็บสถานะพฤติกรรมเชิงลำดับแยกตามกล้องแต่ละตัว
        # ลำดับ (Sequence): 0 = ปกติ, 1 = เข้าใกล้สินค้า, 2 = ถือสินค้าค้างไว้, 3 = พยายามซ่อน
        self.camera_states = {
            "CAM 01": {"score": 0, "sequence_stage": 0, "last_action_time": 0},
            "CAM 02": {"score": 0, "sequence_stage": 0, "last_action_time": 0},
            "CAM 03": {"score": 0, "sequence_stage": 0, "last_action_time": 0},
            "CAM 04": {"score": 0, "sequence_stage": 0, "last_action_time": 0},
        }

    def analyze_frame_objects(self, cam_id, yolov8_results):
        """
        ฟังก์ชันวิเคราะห์พฤติกรรมเชิงลำดับจากผลลัพธ์ของ YOLOv8
        """
        current_time = time.time()
        
        # ดึงรายชื่อคลาสที่ YOLOv8 ตรวจจับได้ในเฟรมนี้
        detected_labels = []
        if len(yolov8_results) > 0 and yolov8_results[0].boxes is not None:
            for box in yolov8_results[0].boxes:
                class_id = int(box.cls[0])
                label = yolov8_results[0].names[class_id]
                detected_labels.append(label)

        # ดึงสถานะปัจจุบันของกล้องตัวนี้มาคำนวณ
        state = self.camera_states[cam_id]
        new_log = None

        # --- LOGIC การคำนวณคะแนนเชิงลำดับ (Sequential Logic) ---
        
        # ขั้นที่ 1: ตรวจพบคน (person) อยู่ใกล้สินค้า
        if "person" in detected_labels and state["sequence_stage"] == 0:
            state["sequence_stage"] = 1
            state["score"] = 1
            state["last_action_time"] = current_time
            new_log = f"[{cam_id}] ตรวจพบผู้ใช้บริการในพื้นที่"

        # ขั้นที่ 2: ตรวจพบการปฏิสัมพันธ์กับวัตถุ (เช่น ตรวจเจอขวดน้ำ, กระเป๋า บรรจุภัณฑ์ต่างๆ)
        elif state["sequence_stage"] == 1:
            # หากมีการตรวจพบวัตถุอื่นๆ เพิ่มเติมในเฟรม ร่วมกับคน
            if len(detected_labels) > 1: 
                state["sequence_stage"] = 2
                state["score"] = 3
                state["last_action_time"] = current_time
                new_log = f"[{cam_id}] มีการปฏิสัมพันธ์หรือหยิบจับสินค้า"
            
            # เคลียร์สถานะหากทิ้งช่วงนานเกินไป (Timeout)
            elif current_time - state["last_action_time"] > 5.0:
                state["sequence_stage"] = 0
                state["score"] = 0

        # ขั้นที่ 3: ตรวจพบพฤติกรรมเสี่ยงสูง หรือวัตถุหายไปในลักษณะที่เข้าข่ายการซ่อน
        elif state["sequence_stage"] == 2:
            # สมมติเงื่อนไข (ตามแต่ที่คุณโมเดล/เทรนคลาสพฤติกรรมไว้ เช่น 'hidden', 'backpack', 'pocket')
            # ในตัวอย่างนี้ระบุว่าถ้าตรวจจับวัตถุบางอย่างจำเพาะเจาะจง หรือพฤติกรรมเข้าเกณฑ์
            if "cell phone" in detected_labels or "backpack" in detected_labels: 
                state["sequence_stage"] = 3
                state["score"] = 5  # คะแนนสูงสุด เสี่ยงสูงสุด
                state["last_action_time"] = current_time
                new_log = f"[{cam_id}] ALERT: ตรวจพบพฤติกรรมเสี่ยงซ่อนสินค้า"
            
            # เคลียร์สถานะหากไม่มีพฤติกรรมต่อเนื่องเกิน 7 วินาที
            elif current_time - state["last_action_time"] > 7.0:
                state["sequence_stage"] = 0
                state["score"] = 0

        # อัปเดตค่ากลับไปยังฐานข้อมูลของกล้อง
        self.camera_states[cam_id] = state
        return state["score"], new_log