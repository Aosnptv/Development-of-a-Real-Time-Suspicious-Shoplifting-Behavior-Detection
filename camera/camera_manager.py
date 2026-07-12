import threading
import time
from camera.camera_device import CameraDevice
from camera.frame_buffer import FrameBuffer
from services.logger import logger

class CameraManager:
    def __init__(self):
        self.devices = {}
        self.buffers = {}
        self.threads = {}
        self._lock = threading.Lock()

    def start_camera(self, camera_id) -> bool:
        """เปิดการทำงานของกล้องในรูปแบบ Background Thread (DoD ข้อ 1, 10)"""
        with self._lock:
            if camera_id in self.devices and self.devices[camera_id].is_running:
                return True

            logger.info(f"Camera {camera_id} Started")
            device = CameraDevice(source=camera_id)
            buffer = FrameBuffer()

            if not device.open():
                logger.error(f"Failed to open Camera {camera_id}")
                return False

            self.devices[camera_id] = device
            self.buffers[camera_id] = buffer
            
            # รันการอ่านเฟรมแบบวนลูปใน Background Thread เพื่อไม่ให้กระทบประสิทธิภาพของหน้า Dashboard
            thread = threading.Thread(target=self._capture_loop, args=(camera_id, device, buffer), daemon=True)
            self.threads[camera_id] = thread
            thread.start()
            return True

    def _capture_loop(self, camera_id, device: CameraDevice, buffer: FrameBuffer):
        """ลูปดึงภาพสดความเร็วสูง ย้ายข้อมูลเข้าสู่ Buffer"""
        while device.is_running:
            success, frame = device.read_frame()
            if success:
                buffer.set_frame(frame)
            else:
                # ถ้าอ่านภาพไม่ได้ (เช่น สายหลุด) ระบบจะทำการดรอปเฟรมและเว้นจังหวะ
                buffer.dropped_frames += 1
                time.sleep(0.03) # นอนรอ 30ms ป้องกัน CPU วิ่ง 100% ววนลูปเปล่า

    def stop_camera(self, camera_id):
        """ปิดการทำงานและเคลียร์ข้อมูลหน่วยความจำ (DoD ข้อ 1, 10, 11)"""
        with self._lock:
            if camera_id in self.devices:
                self.devices[camera_id].release()
                logger.info(f"Camera {camera_id} Stopped")
                
                # ลบ Reference ทิ้งเพื่อให้ระบบจัดการขยะ (Garbage Collector) ทำลายออบเจกต์ ลดปัญหา RAM บวม
                del self.devices[camera_id]
                if camera_id in self.threads:
                    del self.threads[camera_id]

    def restart_camera(self, camera_id):
        """สั่งปิดแล้วเปิดใหม่ทันที (DoD ข้อ 1, 10)"""
        logger.info(f"Camera {camera_id} Restarted")
        self.stop_camera(camera_id)
        time.sleep(0.5) # พักเบรกให้ฮาร์ดแวร์คลายประจุไฟฟ้าแป๊บหนึ่ง
        self.start_camera(camera_id)

    def register_and_start_cameras(self, camera_list):
        """
        เมธอดเชื่อมผสาน (Bridge Method) รองรับโครงสร้างระบบจากแดชบอร์ดหลัก
        รับรายชื่อกล้องเข้ามาแล้วสั่งเริ่มทำงานทีละตัวแบบอัตโนมัติ
        """
        if not camera_list:
            logger.warning("No cameras provided to register and start.")
            return

        for cam in camera_list:
            if isinstance(cam, dict):
                # รองรับโครงสร้างเก่าที่ดึงมาจาก Database ที่เป็น List ของ Dict
                # หากดึงค่า 'source' มาแล้วแปลงเป็นตัวเลขได้ให้ใช้ตัวเลขเพื่อเปิดกล้อง USB
                source = cam.get('source', '0')
                try:
                    cam_id = int(source)
                except ValueError:
                    cam_id = source
            else:
                cam_id = cam
                
            logger.info(f"Registering camera device ID: {cam_id}")
            self.start_camera(cam_id)

    def get_status(self, camera_id) -> dict:
        """สรุปสถานะสุขภาพปัจจุบันของกล้องส่งให้ AppState ดึงไปใช้งานต่อ (DoD ข้อ 1, 6, 9)"""
        with self._lock:
            dev = self.devices.get(camera_id)
            buf = self.buffers.get(camera_id)
            
            if dev and dev.is_running:
                return {
                    "online": True,
                    "fps": round(dev.fps, 2),
                    "resolution": f"{dev.width} x {dev.height}",
                    "frame_count": buf.frame_count if buf else 0,
                    "dropped_frame": buf.dropped_frames if buf else 0,
                    "frame": buf.get_frame() if buf else None
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
            
    def update_app_state_pool(self):
        """
        กวาดข้อมูลสถานะจริงจาก Thread กล้องทั้งหมด 
        แล้วนำไปอัปเดตลงใน AppState.camera_pool แบบ Real-time (DoD ข้อ 9)
        """
        from core.app_state import AppState
        state = AppState()
        
        with self._lock:
            # ตรวจสอบกล้องทุกตัวที่มีการบันทึกไว้ในระบบ
            # ดึงรายชื่อ ID กล้องทั้งหมดที่เคยเรียกผ่าน start_camera
            active_ids = list(self.devices.keys())
            
        for cam_id in active_ids:
            # ดึงข้อมูลสถิติล่าสุด (FPS, Res, เฟรมภาพ) ของกล้องตัวนี้
            status = self.get_status(cam_id)
            
            # แปลง ID ตัวเลขหรือพาร์ทให้เป็นคีย์ข้อความสำหรับแสดงผลบนหน้าจอ เช่น "Camera_0"
            cam_key = f"Camera_{cam_id}"
            
            # อัปเดตข้อมูลเข้าสู่คลังสถานะส่วนกลางของแอปพลิเคชัน
            state.update_camera_pool(cam_key, status)