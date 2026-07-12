import cv2
import datetime

class FrameProcessor:
    @staticmethod
    def process(frame, target_width=640):
        if frame is None:
            return None
            
        # 1. Resize ภาพให้เล็กลงเพื่อลดการโหลดหน่วยความจำของ UI และ AI
        h, w = frame.shape[:2]
        aspect_ratio = h / w
        target_height = int(target_width * aspect_ratio)
        frame_resized = cv2.resize(frame, (target_width, target_height))
        
        # 2. ฝัง Timestamp ลงบนมุมขวาบนของภาพแบบ Real-time
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(
            frame_resized, 
            current_time, 
            (10, 30), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.7, 
            (0, 255, 0), 
            2, 
            cv2.LINE_AA
        )
        
        return frame_resized