import cv2
from PySide6.QtCore import QThread, Signal
import time
import threading
import os
from services.config_service import ConfigManager
from services.logger_service import get_logger
from services.ai_service import AIService
from services.fsm_service import FSMService
from services.database_service import DatabaseService
from services.notification_service import NotificationService

class SubCameraWorker(threading.Thread):
    def __init__(self, idx, status_callback, frame_callback, incident_callback):
        super().__init__()
        self.idx = idx
        self.status_callback = status_callback
        self.frame_callback = frame_callback
        self.incident_callback = incident_callback  # ✅ เก็บค่าไว้ใช้งานในการอัปเดตตาราง UI ล่าสุด
        self.running = False
        self.cap = None
        self.current_fps = 0
        self.fps_counter = 0
        self.last_fps_time = time.time()
        self.daemon = True 
        
        # สำหรับเก็บภาพ BGR ดั้งเดิมไว้บันทึกเป็นหลักฐานตอนแจ้งเตือน
        self.current_bgr_frame = None
        
        # โหลด AI Service, FSM สมองกล ระบบฐานข้อมูล และระบบแจ้งเตือนประจำตัวกล้อง
        try:
            self.ai = AIService()
            self.fsm = FSMService(alert_callback=self.trigger_shoplifting_alert)
            self.db = DatabaseService()
            self.notifier = NotificationService()  # ✅ เปิดใช้งานระบบแจ้งเตือน Telegram สำเร็จ
            self.shelf_roi = (100, 200, 500, 600)  # พิกัดพื้นที่ชั้นวางสินค้าสมมุติ
        except Exception as e:
            self.ai = None
            self.fsm = None
            self.db = None
            self.notifier = None
            print(f"ไม่สามารถโหลดระบบ AI/FSM/DB/Notification สำหรับกล้อง {self.idx} ได้: {e}")

    def trigger_shoplifting_alert(self, person_id, bbox):
        """ฟังก์ชันทำงานอัตโนมัติเมื่อ FSM ตรวจพบพฤติกรรมต้องสงสัยขโมยของ (S5)"""
        print(f"🚨 [กล้องที่ {self.idx}] ตรวจพบพฤติกรรมต้องสงสัย! (Person ID: {person_id})")
        
        if self.current_bgr_frame is not None:
            try:
                # 1. สร้างโฟลเดอร์สำหรับเก็บภาพหลักฐานหากยังไม่มีในเครื่อง
                os.makedirs("evidence", exist_ok=True)
                
                # 2. ตั้งชื่อไฟล์ด้วย วันเวลา_หมายเลขกล้อง_หมายเลขบุคคล
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                image_name = f"evidence/cam_{self.idx}_pid_{person_id}_{timestamp}.jpg"
                
                # 3. บันทึกไฟล์ภาพดิบลงดิสก์คอมพิวเตอร์ก่อน เพื่อให้มีไฟล์อยู่จริงพร้อมส่งต่อ
                cv2.imwrite(image_name, self.current_bgr_frame)
                print(f"📸 บันทึกภาพถ่ายหลักฐานสำเร็จ: {image_name}")
                
                # 4. เขียนต่อท้ายหลังจากบันทึก SQLite สำเร็จ
                if getattr(self, 'db', None):
                    success = self.db.add_incident(camera_id=self.idx, person_id=person_id, image_path=image_name)
                    if success:
                        print(f"💾 บันทึก Log เหตุการณ์ลงฐานข้อมูล SQLite เรียบร้อย!")
                        # ✅ ยิงสัญญาณส่งกลับไปบอกหน้าต่างหลัก UI ให้โหลดดึงตารางใหม่มาแสดงผลสดๆ
                        if self.incident_callback:
                            self.incident_callback()
                
                # 5. สั่งยิงภาพหลักฐานเข้ามือถือผ่าน Telegram ทันทีแบบจังหวะ Real-time Background Thread
                if getattr(self, 'notifier', None):
                    self.notifier.send_alert(
                        camera_id=self.idx, 
                        person_id=person_id, 
                        image_path=image_name
                    )
            except Exception as e:
                print(f"⚠️ เกิดข้อผิดพลาดในการบันทึกหลักฐานหรือแจ้งเตือน: {e}")

    def run(self):
        self.running = True
        next_connect_time = 0
        
        while self.running:
            current_time = time.time()
            
            if self.cap is None or not self.cap.isOpened():
                if current_time < next_connect_time:
                    self.status_callback(self.idx, False)
                    self.frame_callback(self.idx, None)
                    time.sleep(0.3)
                    continue
                
                config = ConfigManager()
                cam_url = config.get(f"camera.cam_{self.idx + 1}", self.idx)
                
                if str(cam_url).isdigit():
                    cam_url = int(cam_url)
                elif cam_url == "":
                    cam_url = self.idx
                
                if isinstance(cam_url, int):
                    self.cap = cv2.VideoCapture(cam_url, cv2.CAP_MSMF)
                else:
                    self.cap = cv2.VideoCapture(cam_url)
                
                if not self.cap.isOpened():
                    self.cap = None
                    next_connect_time = time.time() + 3.0 
                    self.status_callback(self.idx, False)
                    self.frame_callback(self.idx, None)
                    continue
            
            ret, frame = self.cap.read()
            
            if ret and frame is not None:
                self.status_callback(self.idx, True)
                
                # เก็บสำเนาภาพ BGR สีปกติเอาไว้ก่อนนำไปตัดขนาดหรือแปลงสีเพื่อรัน AI
                self.current_bgr_frame = frame.copy()
                
                try:
                    frame = cv2.resize(frame, (640, 480))
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # เปิดใช้งานการตรวจจับและแทร็กวัตถุร่วมกับสมองกล FSM
                    if getattr(self, 'ai', None):
                        frame = self.ai.predict(frame) 
                        
                        # ส่งข้อมูลตำแหน่งวัตถุล่าสุดให้ FSM วิเคราะห์พฤติกรรมในแต่ละเฟรม
                        if getattr(self, 'fsm', None):
                            self.fsm.update(self.ai.latest_tracking_data, self.shelf_roi)
                    
                    if self.running:
                        self.frame_callback(self.idx, frame)
                        
                    self.fps_counter += 1
                    now = time.time()
                    if now - self.last_fps_time >= 1.0:
                        self.current_fps = self.fps_counter
                        self.fps_counter = 0
                        self.last_fps_time = now
                        
                except Exception as e:
                    print(f"⚠️ เกิดข้อผิดพลาดในการประมวลผลภาพกล้อง {self.idx}: {e}")
                
                time.sleep(0.02)
            else:
                print(f"🔴 กล้อง {self.idx} เปิดติดแต่ไม่มีสัญญาณภาพ (ret={ret})")
                if self.cap:
                    self.cap.release()
                self.cap = None
                next_connect_time = time.time() + 3.0
                self.status_callback(self.idx, False)
                self.frame_callback(self.idx, None)

    def stop(self):
        self.running = False


class CameraWorker(QThread):
    frame_ready = Signal(int, object)
    info_updated = Signal(int, str, float, int, int) 
    # ✅ สัญญาณหลักสำหรับเชื่อมโยงไปสั่งให้ UI หน้า Dashboard รีโหลดตารางประวัติใหม่
    incident_triggered = Signal()
    
    def __init__(self):
        super().__init__()
        self.sub_workers = {}
        self.active_indices = [0, 1, 2, 3] 
        self._online_cameras = set()

    def set_active_cameras(self, indices):
        self.active_indices = indices
        for idx in self.active_indices:
            if idx not in self.sub_workers:
                # ✅ ส่งตัวยิงสัญญาณเสี่ยงภัยผูกเข้าไปที่ลูกทีมย่อยเพื่อส่งสัญญาณข้าม Thread ได้อย่างปลอดภัย
                worker = SubCameraWorker(idx, self._update_status, self._handle_frame, self.incident_triggered.emit)
                self.sub_workers[idx] = worker
                worker.start()
                
        for idx in list(self.sub_workers.keys()):
            if idx not in self.active_indices:
                self.sub_workers[idx].stop()
                del self.sub_workers[idx]
                if idx in self._online_cameras:
                    self._online_cameras.remove(idx)

    def _update_status(self, idx, is_online):
        if is_online:
            self._online_cameras.add(idx)
            status_str = "Online"
        else:
            if idx in self._online_cameras:
                self._online_cameras.remove(idx)
            status_str = "Offline"
            
        worker = self.sub_workers.get(idx)
        fps = worker.current_fps if worker else 0.0
        self.info_updated.emit(idx, status_str, float(fps), 640, 480)

    def _handle_frame(self, idx, frame):
        self.frame_ready.emit(idx, frame)

    def start_camera(self):
        self.set_active_cameras(self.active_indices)

    def stop_camera(self):
        for worker in self.sub_workers.values():
            worker.stop()
        self.sub_workers.clear()
        self._online_cameras.clear()

    @property
    def available_cameras(self):
        return list(self._online_cameras)

    @property
    def current_fps(self):
        fps_list = [w.current_fps for w in self.sub_workers.values() if w.current_fps > 0]
        return int(sum(fps_list) / len(fps_list)) if fps_list else 0
        
    @current_fps.setter
    def current_fps(self, value):
        pass


# ==========================================
# ส่วนทดสอบระบบ (เรียกใช้โดยตรงสำหรับ Debug)
# ==========================================
logger = get_logger("CameraService")
config = ConfigManager()

def start_camera_test():
    """ฟังก์ชันสำหรับเทสต์ระบบกล้องแยกต่างหาก"""
    try:
        cam_1_url = config.get("camera.cam_1")
        logger.info(f"กำลังทดสอบเชื่อมต่อกล้อง: {cam_1_url}")
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการเปิดกล้อง: {str(e)}")