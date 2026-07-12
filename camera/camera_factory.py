from camera.camera_device import CameraDevice

class CameraFactory:
    @staticmethod
    def create_camera(cam_id: int, name: str, source: str) -> CameraDevice:
        return CameraDevice(cam_id, name, source)