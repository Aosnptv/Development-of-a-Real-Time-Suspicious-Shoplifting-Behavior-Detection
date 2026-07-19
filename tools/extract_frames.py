import cv2
import os

def extract_frames_from_video(video_path, output_dir, target_fps=3):
    """
    สกัดภาพจากวิดีโอตาม FPS ที่กำหนด
    - video_path: ตำแหน่งไฟล์วิดีโอ
    - output_dir: โฟลเดอร์สำหรับบันทึกภาพ
    - target_fps: จำนวนภาพที่ต้องการดึงออกมาใน 1 วินาที (แนะนำ 2-5 ภาพ)
    """
    # สร้างโฟลเดอร์ถ้ายังไม่มี
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"🔴 ไม่สามารถเปิดวิดีโอได้: {video_path}")
        return

    # หาค่า FPS ดั้งเดิมของวิดีโอ (เช่น 30 หรือ 60 fps)
    original_fps = int(cap.get(cv2.CAP_PROP_FPS))
    if original_fps == 0:
        original_fps = 30 # ป้องกันบั๊กกรณีวิดีโออ่านค่าไม่ได้

    # คำนวณระยะห่างของเฟรมที่ต้องดึง (ข้ามกี่เฟรมถึงจะดึง 1 รูป)
    frame_interval = max(1, round(original_fps / target_fps))
    
    # ดึงชื่อไฟล์วิดีโอแบบไม่เอานามสกุล
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    
    frame_count = 0
    saved_count = 0

    print(f"🎬 กำลังประมวลผล: {video_name} (Original FPS: {original_fps}, ดึงออก: {target_fps} รูป/วินาที)")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # บันทึกเฉพาะเฟรมที่ตรงกับจังหวะที่คำนวณไว้
        if frame_count % frame_interval == 0:
            # ตั้งชื่อไฟล์: ชื่อวิดีโอ_frame_0001.jpg
            filename = f"{video_name}_frame_{saved_count:04d}.jpg"
            filepath = os.path.join(output_dir, filename)
            
            # บันทึกเป็นภาพคุณภาพสูง
            cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, 100])
            saved_count += 1

        frame_count += 1

    cap.release()
    print(f"✅ สำเร็จ! ได้ทั้งหมด {saved_count} ภาพ ถูกบันทึกไว้ที่: {output_dir}\n")


def process_folder(input_folder, output_folder, target_fps=3):
    """วนลูปประมวลผลทุกวิดีโอในโฟลเดอร์แบบอัตโนมัติ"""
    valid_extensions = ('.mp4', '.avi', '.mov', '.mkv')
    
    if not os.path.exists(input_folder):
        print(f"⚠️ ไม่พบโฟลเดอร์ต้นทาง: {input_folder} (กรุณาสร้างและใส่วิดีโอลงไป)")
        return
        
    for file in os.listdir(input_folder):
        if file.lower().endswith(valid_extensions):
            video_path = os.path.join(input_folder, file)
            extract_frames_from_video(video_path, output_folder, target_fps)

# ==========================================
# วิธีใช้งาน
# ==========================================
if __name__ == "__main__":
    # 1. โฟลเดอร์ที่เก็บไฟล์วิดีโอของคุณ (เช่น คลิปเดิน, หยิบของ)
    INPUT_VIDEOS_DIR = "videos_raw"      
    
    # 2. โฟลเดอร์เป้าหมายที่จะเอาภาพไปกองรวมกันรอ Label
    OUTPUT_FRAMES_DIR = "dataset/images/raw_extracted" 
    
    # 3. จำนวนภาพที่อยากได้ใน 1 วินาที (ถ้าน้อยไปให้ปรับขึ้น มากไปให้ปรับลง)
    TARGET_FPS = 3                   
    
    print("🚀 เริ่มกระบวนการสกัดภาพจากวิดีโอ...")
    process_folder(INPUT_VIDEOS_DIR, OUTPUT_FRAMES_DIR, TARGET_FPS)