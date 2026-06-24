import streamlit as st
import cv2
from ultralytics import YOLO

st.set_page_config(page_title="ระบบตรวจจับขโมย", layout="wide")
st.title("ระบบเฝ้าระวังพฤติกรรมเสี่ยง (Shoplifting Detection)")

# โหลดโมเดล (ใช้ st.cache_resource เพื่อไม่ให้โหลดใหม่ทุกครั้ง)
@st.cache_resource
def load_model():
    return YOLO('yolov8n.pt')

model = load_model()

# แบ่งหน้าจอ
col1, col2 = st.columns([3, 1])

with col1:
    st.header("วิดีโอเรียลไทม์")
    frame_placeholder = st.empty() # พื้นที่สำหรับแสดงวิดีโอ

with col2:
    st.header("สถานะระบบ")
    score_text = st.empty()
    alert_placeholder = st.empty()

# ปุ่มเปิด/ปิดกล้อง
run = st.checkbox("เปิดกล้องประมวลผล")

if run:
    cap = cv2.VideoCapture(0)
    score = 0
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            st.error("ไม่สามารถเปิดกล้องได้")
            break
            
        # ประมวลผล YOLO
        results = model(frame)
        annotated_frame = results[0].plot()
        
        # แสดงวิดีโอใน Streamlit โดยต้องแปลงสีก่อน
        frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        frame_placeholder.image(frame_rgb, channels="RGB")
        
        # สมมติระบบจำลองการนับคะแนน (ในของจริงต้องดึง Bounding box มาเข้า logic.py)
        # score += 0.1 
        # score_text.metric("Suspicion Score", f"{int(score)} / 5")
        
        if score >= 5:
            alert_placeholder.error("🚨 ตรวจพบพฤติกรรมน่าสงสัย!")
            # เรียกใช้ send_telegram_alert(...) ตรงนี้
            # break (หรือสั่งรีเซ็ตคะแนน)
            
    cap.release()