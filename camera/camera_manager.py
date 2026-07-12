import threading
import time
from camera.camera_device import CameraDevice
from camera.frame_buffer import FrameBuffer
from services.logger import logger

class CameraManager:
    def __init__(self):
        self.active_devices = {}
        self.active_buffers = {}
        self.active_threads = {}
        self._lock = threading.Lock()

    def start_camera_pipeline(self, camera_id) -> bool:
        """สั่งเปิดท่อสัญญาณกล้องแยกเป็น Background Thread อิสระ"""
        with self._lock:
            # หากกล้องนี้รันอยู่แล้ว ไม่ต้องสั่งเปิดซ้ำ
            if camera_id in self.active_devices and self.active_devices[camera_id].is_running:
                return True

            device = CameraDevice(source=camera_id)
            buffer = FrameBuffer()

            if not device.open_hardware():
                logger.error(f"[Pipeline] Failed to open camera device: {camera_id}")
                return False

            self.active_devices[camera_id] = device
            self.active_buffers[camera_id] = buffer
            
            # สั่งแยกเธรดออกไปดึงภาพสดที่ความเร็วสูงสุดของกล้อง (30 FPS)
            thread = threading.Thread(
                target=self._capture_worker_loop, 
                args=(camera_id, device, buffer), 
                daemon=True
            )
            self.active_threads[camera_id] = thread
            thread.start()
            
            logger.info(f"Camera {camera_id} Started")
            return True

    def _capture_worker_loop(self, camera_id, device: CameraDevice, buffer: FrameBuffer):
        """ลูปทำงานเบื้องหลัง ดึงภาพจากกล้องโยนใส่บัฟเฟอร์แบบต่อเนื่อง"""
        while device.is_running:
            success, frame = device.grab_frame()
            if success:
                buffer.set_frame(frame)
            else:
                buffer.set_frame(None)
                time.sleep(0.03) # นอนพักสั้นๆ ป้องกัน CPU โอเวอร์โหลดกรณีสายกล้องหลุด

    def stop_camera_pipeline(self, camera_id):
        """สั่งดับเครื่องยนต์ ล้างท่อสัญญาณ และทำลาย Object เพื่อป้องกันแรมบวม"""
        with self._lock:
            if camera_id in self.active_devices:
                self.active_devices[camera_id].close_hardware()
                logger.info(f"Camera {camera_id} Stopped")
                
                # ลบหน่วยความจำอ้างอิงทั้งหมดออกเพื่อให้ Garbage Collector ทำลายทิ้ง
                del self.active_devices[camera_id]
                if camera_id in self.active_buffers:
                    del self.active_buffers[camera_id]
                if camera_id in self.active_threads:
                    del self.active_threads[camera_id]

    def restart_camera_pipeline(self, camera_id):
        """สั่งปิดกระบวนการแล้วเริ่มต้นใหม่ทันที เพื่อกู้คืนสัญญาณภาพ"""
        logger.info(f"Camera {camera_id} Restarted")
        self.stop_camera_pipeline(camera_id)
        time.sleep(0.5)
        self.start_camera_pipeline(camera_id)

    def register_and_start_cameras(self, camera_list):
        """
        [Bridge Method] รองรับโครงสร้างระบบจากแดชบอร์ดหลัก 
        รับรายชื่อกล้องเข้ามาแล้วสั่งเริ่มทำงานทีละตัวผ่านท่อ Pipeline
        """
        if not camera_list:
            logger.warning("[Pipeline] No cameras provided to register and start.")
            return

        for cam in camera_list:
            if isinstance(cam, dict):
                source = cam.get('source', '0')
                try:
                    cam_id = int(source)
                except ValueError:
                    cam_id = source
            else:
                cam_id = cam
                
            logger.info(f"[Pipeline] Registering and initializing camera device ID: {cam_id}")
            self.start_camera_pipeline(cam_id)

    def update_app_state_pool(self):
        """
        กวาดข้อมูลสถานะจริงจาก Thread กล้องทั้งหมด 
        แล้วนำไปอัปเดตลงใน AppState.camera_pool แบบ Real-time (DoD ข้อ 9)
        """
        from core.app_state import AppState
        state = AppState()
        
        with self._lock:
            active_ids = list(self.active_devices.keys())
            
        for cam_id in active_ids:
            status = self.get_pipeline_snapshot(cam_id)
            cam_key = f"Camera_{cam_id}"
            state.update_camera_pool(cam_key, status)

    def get_pipeline_snapshot(self, camera_id) -> dict:
        """ส่งรายงานสุขภาพล่าสุดของ Pipeline ไปให้แอปส่วนกลางนำไปวินิจฉัย"""
        with self._lock:
            dev = self.active_devices.get(camera_id)
            buf = self.active_buffers.get(camera_id)
            
            if dev and dev.is_running:
                return {
                    "online": True,
                    "fps": round(dev.actual_fps, 2),
                    "resolution": f"{dev.width} x {dev.height}",
                    "frame_count": buf.frame_count if buf else 0,
                    "dropped_frame": buf.dropped_frame_count if buf else 0,
                    "frame": buf.get_latest_frame() if buf else None
                }
            else:
                return {
                    "online": False,
                    "fps": 0.0,
                    "resolution": "0 x 0",
                    "frame_count": 0,
                    "dropped_frame": 0,
                    "frame": None
                }