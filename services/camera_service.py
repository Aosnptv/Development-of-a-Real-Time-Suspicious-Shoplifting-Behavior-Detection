import cv2
from PySide6.QtCore import QThread, Signal
import time
import threading

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
                
                self.cap = cv2.VideoCapture(self.idx) 
                if not self.cap.isOpened():
                    self.cap = None
                    next_connect_time = time.time() + 30.0 
                    self.status_callback(self.idx, False)
                    self.frame_callback(self.idx, None)
                    continue
            
            ret, frame = self.cap.read()
            if ret:
                self.status_callback(self.idx, True)
                
                # 🟢 แก้จุด CPU 100%: ย่อขนาดภาพให้พอดีจากหลังบ้านด้วย C++ ไม่ให้เป็นภาระ UI หลัก
                frame = cv2.resize(frame, (640, 480))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                if self.running:
                    self.frame_callback(self.idx, frame)
                
                self.fps_counter += 1
                now = time.time()
                if now - self.last_fps_time >= 1.0:
                    self.current_fps = self.fps_counter
                    self.fps_counter = 0
                    self.last_fps_time = now
                
                time.sleep(0.02)
            else:
                if self.cap:
                    self.cap.release()
                self.cap = None
                next_connect_time = time.time() + 30.0
                self.status_callback(self.idx, False)
                self.frame_callback(self.idx, None)
                
        if self.cap:
            self.cap.release()
            self.cap = None

    def stop(self):
        self.running = False

class CameraWorker(QThread):
    frame_ready = Signal(int, object)
    
    def __init__(self):
        super().__init__()
        self.sub_workers = {}
        self.active_indices = [0, 1]
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
        else:
            if idx in self._online_cameras:
                self._online_cameras.remove(idx)

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