import math
import time

class FSMService:
    def __init__(self, alert_callback=None):
        # alert_callback: ฟังก์ชันที่จะให้เรียกใช้เมื่อยืนยันเหตุการณ์ S5 (เช่น สั่งแคปภาพ/ส่ง Telegram)
        self.alert_callback = alert_callback
        
        # โครงสร้างเก็บสถานะแยกตาม Person ID: { person_id: { "state": "S0", "product_id": None, "s5_start_time": None } }
        self.person_states = {}
        
        # เกณฑ์ตั้งค่าระยะห่างพิกัด (Thresholds) - สามารถปรับเปลี่ยนให้เหมาะกับระยะกล้องจริงได้
        self.THRESHOLD_APPROACH = 80.0    # ระยะห่าง Hand กับ Product ที่ถือว่าใกล้ (S1)
        self.THRESHOLD_NEAR_BODY = 100.0  # ระยะห่าง Product กับ Person ที่ถือว่าแนบลำตัว (S3)
        self.S5_CONFIRM_TIME = 2.5        # ต้องค้างอยู่สถานะ S5 นาน 2.5 วินาทีถึงจะยืนยันว่าเป็นเหตุการณ์จริง

    def _get_distance(self, p1, p2):
        """คำนวณระยะห่าง Euclidean Distance ระหว่างจุดสองจุด"""
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

    def _is_point_in_box(self, point, box):
        """ตรวจสอบว่าจุดศูนย์กลางอยู่ในกรอบ Bounding Box หรือไม่"""
        px, py = point
        x1, y1, x2, y2 = box
        return x1 <= px <= x2 and y1 <= py <= y2

    def update(self, tracking_data, shelf_roi):
        """
        ฟังก์ชันอัปเดตและคำนวณสถานะ FSM ในทุกๆ เฟรมภาพ
        tracking_data: ข้อมูลจาก self.latest_tracking_data ของ AIService
        shelf_roi: พิกัดพื้นที่ชั้นวางข้อมูลสินค้า (x1, y1, x2, y2)
        """
        current_time = time.time()
        
        persons = tracking_data.get("persons", [])
        hands = tracking_data.get("hands", [])
        products = tracking_data.get("products", [])
        baskets = tracking_data.get("baskets", [])

        # วนลูปตรวจสอบทุก Person ID ที่ระบบตรวจจับได้ในเฟรมนี้ (Primary Reference)
        for person in persons:
            pid = person["id"]
            if pid is None:
                continue
                
            # ถ้ายังไม่มีข้อมูล Person นี้ในระบบ FSM ให้ลงทะเบียนเริ่มต้นที่ S0 (Normal)
            if pid not in self.person_states:
                self.person_states[pid] = {
                    "state": "S0",
                    "associated_product_id": None,
                    "s5_start_time": None,
                    "last_seen_product_pos": None
                }
                
            p_state = self.person_states[pid]
            p_center = person["center"]
            p_box = person["box"]

            # 🔍 [Object Association] ค้นหา Hand และ Product ที่อยู่ใกล้ตัว Person นี้ที่สุด
            my_hands = [h for h in hands if self._is_point_in_box(h["center"], p_box) or self._get_distance(h["center"], p_center) < 150]
            
            # --- กลไกเปลี่ยนสถานะ FSM (State Transition Logic) ---
            
            # 🟢 S0 (Normal) -> สินค้าอยู่บนชั้นวาง
            if p_state["state"] == "S0":
                for prod in products:
                    if self._is_point_in_box(prod["center"], shelf_roi):
                        # สแกนดูว่ามีมือขยับเข้าใกล้สินค้าชิ้นนี้ไหม
                        for hand in my_hands:
                            dist = self._get_distance(hand["center"], prod["center"])
                            if dist < self.THRESHOLD_APPROACH:
                                p_state["state"] = "S1"
                                p_state["associated_product_id"] = prod["id"]
                                print(f"[FSM] 👤 Person {pid} เปลี่ยนสถานะ: S0 -> S1 (Approaching Product {prod['id']})")
                                break

            # 🟡 S1 (Approaching) -> มือเคลื่อนเข้าใกล้สินค้า
            elif p_state["state"] == "S1":
                target_prod = next((p for p in products if p["id"] == p_state["associated_product_id"]), None)
                if target_prod:
                    p_state["last_seen_product_pos"] = target_prod["center"]
                    # ถ้าจุดศูนย์กลางของสินค้าชิ้นนั้นหลุดออกจากพื้นที่ชั้นวาง (Shelf ROI)
                    if not self._is_point_in_box(target_prod["center"], shelf_roi):
                        p_state["state"] = "S2"
                        print(f"[FSM] 👤 Person {pid} เปลี่ยนสถานะ: S1 -> S2 (Picked Product {target_prod['id']})")
                else:
                    # หากสินค้าหายไปดื้อๆ ให้เด้งกลับไป S0
                    p_state["state"] = "S0"

            # 🟠 S2 (Picked) -> หยิบสินค้าออกจากชั้นวางแล้ว
            elif p_state["state"] == "S2":
                target_prod = next((p for p in products if p["id"] == p_state["associated_product_id"]), None)
                if target_prod:
                    p_state["last_seen_product_pos"] = target_prod["center"]
                    # คำนวณระยะห่างระหว่างสินค้ากับลำตัวบุคคล
                    dist_to_body = self._get_distance(target_prod["center"], p_center)
                    if dist_to_body < self.THRESHOLD_NEAR_BODY:
                        p_state["state"] = "S3"
                        print(f"[FSM] 👤 Person {pid} เปลี่ยนสถานะ: S2 -> S3 (Product Near Body)")
                else:
                    p_state["state"] = "S0"

            # 🔴 S3 (Near Body) -> สินค้าอยู่แนบลำตัว
            elif p_state["state"] == "S3":
                target_prod = next((p for p in products if p["id"] == p_state["associated_product_id"]), None)
                
                # ตรวจสอบการผ่านตะกร้า (Basket Verification) ก่อน
                if target_prod:
                    p_state["last_seen_product_pos"] = target_prod["center"]
                    for basket in baskets:
                        if self._is_point_in_box(target_prod["center"], basket["box"]):
                            p_state["state"] = "S0"  # ปลอดภัย สินค้าลงตะกร้า กลับสู่สถานะปกติ
                            p_state["associated_product_id"] = None
                            print(f"[FSM] 👤 Person {pid} เปลี่ยนสถานะ: S3 -> S4 -> S0 (Verified in Basket)")
                            break
                
                # 🚨 เกิดการหายไปของสินค้า (Object Disappearance) ในขณะอยู่ใกล้ลำตัว
                else:
                    # เช็คพิกัดสุดท้ายก่อนหายไปว่าไม่ได้จงใจหย่อนลงตะกร้า
                    in_basket = False
                    last_pos = p_state["last_seen_product_pos"]
                    if last_pos:
                        for basket in baskets:
                            if self._is_point_in_box(last_pos, basket["box"]):
                                in_basket = True
                                break
                    
                    if not in_basket:
                        p_state["state"] = "S5"
                        p_state["s5_start_time"] = current_time
                        print(f"[FSM] ⚠️ 👤 Person {pid} เปลี่ยนสถานะ: S3 -> S5 (Suspected Concealment!)")
                    else:
                        p_state["state"] = "S0"

            # 🚨 S5 (Suspected Concealment) -> ต้องค้างอยู่ตามเวลาที่กำหนดเพื่อยืนยันเหตุการณ์เสี่ยงจริง
            elif p_state["state"] == "S5":
                # ตรวจดูว่าสินค้าย้อนกลับมาปรากฏตัวใหม่หรือไม่ (เผื่อโดนบังชั่วคราว)
                target_prod = next((p for p in products if p["id"] == p_state["associated_product_id"]), None)
                if target_prod:
                    p_state["state"] = "S3"  # สินค้าโผล่กลับมา ดึงกลับไป S3
                    p_state["s5_start_time"] = None
                    print(f"[FSM] ℹ️ 👤 Person {pid} สินค้าปรากฏขึ้นอีกครั้ง: S5 -> S3")
                else:
                    # คำนวณระยะเวลาที่ค้างอยู่ในสถานะ S5
                    elapsed = current_time - p_state["s5_start_time"]
                    if elapsed >= self.S5_CONFIRM_TIME:
                        print(f"🚨 [ALERT] !!ตรวจพบพฤติกรรมต้องสงสัยขโมยสินค้าโดย Person ID: {pid}!!")
                        if self.alert_callback:
                            self.alert_callback(pid, person["box"])
                        
                        # รีเซ็ตสถานะหลังแจ้งเตือนเสร็จเพื่อไม่ให้ยิงแจ้งเตือนซ้ำๆ ทุกเฟรม
                        p_state["state"] = "S0"
                        p_state["associated_product_id"] = None
                        p_state["s5_start_time"] = None

        # 🧹 ล้างข้อมูล Person ID ที่เดินหลุดออกไปจากกล้องแล้ว เพื่อประหยัด Memory
        active_pids = [p["id"] for p in persons if p["id"] is not None]
        for stored_pid in list(self.person_states.keys()):
            if stored_pid not in active_pids:
                # เผื่อหลุดเฟรมไปแว๊บเดียวช่วงกำลังจับผิด ให้โอกาสคงสถานะ S5 ไว้ก่อนสักครู่
                if self.person_states[stored_pid]["state"] != "S5":
                    del self.person_states[stored_pid]