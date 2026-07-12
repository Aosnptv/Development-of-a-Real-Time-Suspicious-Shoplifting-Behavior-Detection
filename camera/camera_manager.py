import threading
from camera.camera_factory import CameraFactory
from core.app_state import AppState
from services.logger import logger

class CameraManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CameraManager, cls).__new__(cls)
                cls._instance._active_devices = {}
        return cls._instance

    def register_and_start_cameras(self, camera_list: list):
        """รับรายชื่อกล้องจาก Database และสั่งเปิดการทำงานแบบ Threading ทันที"""
        for cam in camera_list:
            cam_name = cam["name"]
            if cam_name not in self._active_devices:
                device = CameraFactory.create_camera(cam["id"], cam_name, cam["source"])
                device.start()
                self._active_devices[cam_name] = device
                logger.info(f"Registered camera device: {cam_name}")

    def shutdown_all_cameras(self):
        for name, device in list(self._active_devices.items()):
            device.stop()
            del self._active_devices[name]
        logger.info("All registered cameras have been safely shut down.")

    def restart_camera(self, name: str):
        if name in self._active_devices:
            device = self._active_devices[name]
            device.stop()
            device.start()
            logger.warning(f"Camera {name} was manually restarted.")

    def update_app_state_pool(self):
        """ฟังก์ชันที่จะถูกเรียกใน Loop หลักเพื่ออัปเดตภาพและเมทริกซ์เข้า AppState"""
        state = AppState()
        for name, device in self._active_devices.items():
            report = device.get_status_report()
            
            # โยนทั้งสเปกกล้องและตัวแปร Frame ภาพเข้าคลังข้อมูลส่วนกลาง
            state.update_camera_pool(name, {
                "online": report["online"],
                "fps": report["fps"],
                "resolution": report["resolution"],
                "frame": device.get_latest_frame()
            })