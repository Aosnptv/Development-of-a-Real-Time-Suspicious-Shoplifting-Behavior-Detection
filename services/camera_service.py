import cv2
from PySide6.QtCore import QThread, Signal
import time
import threading
from services.config_service import ConfigManager
from services.logger_service import get_logger
from services.ai_service import AIService

class SubCameraWorker(threading.Thread):
    def __init__(self, idx, status_callback, frame_callback):
        super().__init__()
        self.idx = idx
        self.status_callback = status_callback
        self.frame_callback = frame_callback
        self.running = False
        self.cap = None
        self.current_fps = 0
        self.fps_counter = 0
        self.last_fps_time = time.time()
        self.daemon = True 
        
        # โหลด AI Service ตามปกติ
        try:
            self.ai = AIService()
        except Exception as e:
            self.ai = None
            print(f"ไม่สามารถโหลด AI สำหรับกล้อง {self.idx} ได้: {e}")

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
                
                try:
                    frame = cv2.resize(frame, (640, 480))
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # 🛑 เราปิด AI ไว้ก่อนจนกว่าภาพเพียวๆ จะแสดงบนจอสำเร็จ
                    # if self.ai:
                    #     results = self.ai.predict(frame) 
                    
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
    
    def __init__(self):
        super().__init__()
        self.sub_workers = {}
        self.active_indices = [0, 1, 2, 3] 
        self._online_cameras = set()

    def set_active_cameras(self, indices):
        self.active_indices = indices
        for idx in self.active_indices:
            if idx not in self.sub_workers:
                worker = SubCameraWorker(idx, self._update_status, self._handle_frame)
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
# ส่วนทดสอบระบบ (เรียกใช้โดยตรง)
# ==========================================
logger = get_logger("CameraService")
config = ConfigManager()

def start_camera_test():
    """ฟังก์ชันสำหรับเทสต์ระบบกล้องแยกต่างหาก (เผื่อเอาไว้รัน Debug)"""
    try:
        cam_1_url = config.get("camera.cam_1")
        logger.info(f"กำลังทดสอบเชื่อมต่อกล้อง: {cam_1_url}")
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการเปิดกล้อง: {str(e)}")