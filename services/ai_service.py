import os
import cv2

class AIService:
    def __init__(self, model_path="runs/detect/shoplifting_model_v1-5/weights/best.pt"):  
        self.model_path = model_path
        self.model = None
        
        # ตัวแปรสำหรับเก็บข้อมูล Tracking ล่าสุด เพื่อส่งต่อให้ระบบ FSM ประมวลผล
        self.latest_tracking_data = {
            "persons": [],
            "hands": [],
            "products": [],
            "baskets": []
        }
        
        # โหลดโมเดลตอนเริ่มต้น
        self.load_model()

    def load_model(self):
        """โหลดโมเดล AI อย่างปลอดภัย หากไม่มีไฟล์จะเข้าสู่ Simulation Mode"""
        print(f"[AIService] กำลังโหลดโมเดล YOLO จาก: {self.model_path}")
        try:
            from ultralytics import YOLO
            if os.path.exists(self.model_path):
                self.model = YOLO(self.model_path)
                print("[AIService] 🟢 โหลดโมเดลและระบบติดตามวัตถุสำเร็จ!")
            else:
                raise FileNotFoundError(f"ไม่พบไฟล์โมเดลที่ตำแหน่ง {self.model_path}")
        except Exception as e:
            print(f"[AIService] ⚠️ [ERROR] เกิดข้อผิดพลาดในการโหลดโมเดล: {e}")
            print("[AIService] ℹ️ เปลี่ยนเข้าสู่ระบบจำลอง (Simulation Mode) ชั่วคราว")
            self.model = None

    def predict(self, frame):
        """ฟังก์ชันตรวจจับและติดตามวัตถุ (YOLO11s + ByteTrack) พร้อมเงื่อนไขพิเศษ"""
        # กรณีโหมดจำลอง (ไม่มีโมเดล) ส่งภาพเปล่ากลับไปเพื่อไม่ให้ UI พัง
        if self.model is None:
            return frame 
            
        # 1. รันการติดตามวัตถุด้วย ByteTrack (persist=True หมายถึงให้จำ ID ข้ามเฟรมต่อเนื่อง)
        results = self.model.track(frame, persist=True, conf=0.40, tracker="bytetrack.yaml")
        
        # สร้างภาพสำเนาสำหรับนำมาวาดกรอบแบบกำหนดเอง (Custom Drawing)
        annotated_frame = frame.copy()
        
        # เคลียร์ข้อมูล Tracking รอบเก่าออกก่อน
        detected_persons = []
        detected_hands = []
        detected_products = []
        detected_baskets = []
        
        # ตรวจสอบว่ามีวัตถุถูกตรวจจับเจอในเฟรมนี้หรือไม่
        if results and results[0].boxes is not None:
            boxes = results[0].boxes
            
            # --- รอบที่ 1: คัดแยกวัตถุออกเป็นหมวดหมู่ และหาขนาดของ "มือ" ---
            for box in boxes:
                # ดึงพิกัด (x1, y1, x2, y2)
                xyxy = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = map(int, xyxy)
                
                cls = int(box.cls[0].item())        # หมายเลขคลาส (0=person, 1=hand, 2=product, 3=basket)
                conf = float(box.conf[0].item())     # ค่าความมั่นใจ
                
                # ดึง Tracking ID (ถ้าเฟรมแรกๆ หรือหลุดแทร็ก ค่าอาจเป็น None)
                track_id = int(box.id[0].item()) if box.id is not None else None
                
                # คำนวณขนาดพื้นที่ Bounding Box (กว้าง x สูง)
                area = (x2 - x1) * (y2 - y1)
                
                obj_data = {
                    "box": (x1, y1, x2, y2),
                    "center": ((x1 + x2) // 2, (y1 + y2) // 2),
                    "id": track_id,
                    "conf": conf,
                    "area": area
                }
                
                if cls == 0:
                    detected_persons.append(obj_data)
                elif cls == 1:
                    detected_hands.append(obj_data)
                elif cls == 2:
                    detected_products.append(obj_data)
                elif cls == 3:
                    detected_baskets.append(obj_data)

            # หาขนาดของ Bounding Box ของมือที่ใหญ่ที่สุดในเฟรมนี้ (ถ้าไม่มีมือ ให้เกณฑ์ขั้นต่ำเป็น 0)
            max_hand_area = max([h["area"] for h in detected_hands]) if detected_hands else 0

            # --- รอบที่ 2: ใช้เงื่อนไขพิเศษกรองขนาดสินค้า และเริ่มวาดกรอบลงบนหน้าจอ ---
            # กรองคลาส Product เฉพาะชิ้นที่มีขนาดใหญ่กว่า Hand เพื่อลด Noise ตามขอบเขตโปรเจกต์
            filtered_products = [p for p in detected_products if p["area"] > max_hand_area]

            # 🎨 วาดกรอบ Person (สีน้ำเงิน) - มี Tracking ID
            for p in detected_persons:
                x1, y1, x2, y2 = p["box"]
                tid = p["id"] if p["id"] is not None else "..."
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                cv2.putText(annotated_frame, f"Person ID:{tid}", (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

            # 🎨 วาดกรอบ Hand (สีเขียว) - มี Tracking ID
            for h in detected_hands:
                x1, y1, x2, y2 = h["box"]
                tid = h["id"] if h["id"] is not None else "..."
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(annotated_frame, f"Hand ID:{tid}", (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # 🎨 วาดกรอบ Product ที่ผ่านการกรองขนาดแล้ว (สีส้ม) - มี Tracking ID
            for p in filtered_products:
                x1, y1, x2, y2 = p["box"]
                tid = p["id"] if p["id"] is not None else "..."
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 165, 255), 2)
                cv2.putText(annotated_frame, f"Product ID:{tid}", (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)

            # 🎨 วาดกรอบ Basket (สีแดง) - ตีกรอบพิกัดเท่านั้น **ไม่มีการ Tracking ID** ตามเงื่อนไข
            for b in detected_baskets:
                x1, y1, x2, y2 = b["box"]
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(annotated_frame, "Basket", (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            # อัปเดตข้อมูลชุดล่าสุดเก็บไว้ใน Object เพื่อรอให้ระบบอื่นดึงไปใช้ต่อ
            self.latest_tracking_data = {
                "persons": detected_persons,
                "hands": detected_hands,
                "products": filtered_products,
                "baskets": detected_baskets
            }

        return annotated_frame