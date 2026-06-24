import streamlit as st
import cv2
import numpy as np
from ultralytics import YOLO
import time

# 1. ตั้งค่าหน้าเว็บให้เป็นแบบเต็มจอ (Wide) และเปลี่ยนชื่อแท็บ
st.set_page_config(page_title="CCTV Loss Prevention System", layout="wide")

# ตกแต่งสไตล์ CSS ให้ดูเหมือนหน้าจอ CCTV จริงๆ (โทนสีเข้ม)
st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; color: #E0E6ED; }
    .status-card {
        background-color: #1A1F2C; padding: 15px; border-radius: 8px;
        border-left: 5px solid #00E676; margin-bottom: 10px;
    }
    .alert-card {
        background-color: #2C1A1A; padding: 15px; border-radius: 8px;
        border-left: 5px solid #FF1744; margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📹 ระบบห้องควบคุมกล้องวงจรปิดอัจฉริยะ (AI CCTV Control Room)")
st.caption("ระบบตรวจจับพฤติกรรมเสี่ยงต่อการซ่อนสินค้าด้วย Deep Learning สำหรับกล้องหลายตัว")

# 2. โหลดโมเดล YOLO
@st.cache_resource
def load_model():
    return YOLO('yolov8n.pt')  # เปลี่ยนเป็น Path โมเดลของคุณ เช่น 'best.pt'

model = load_model()

# 3. เมนูด้านข้าง (Sidebar) สำหรับควบคุมระบบ
st.sidebar.header("🕹️ แผงควบคุมกล้อง")
run_system = st.sidebar.checkbox("เริ่มต้นทำงานระบบ (Start CCTV)", value=False)

st.sidebar.markdown("---")
view_mode = st.sidebar.radio(
    "🖥️ รูปแบบการแสดงผล (Layout Mode)",
    ["ดูมุมกล้องรวม (Grid View)", "เลือกสลับมุมกล้อง (Single View)"]
)

# ตัวเลือกสำหรับโหมดสลับมุมกล้อง
selected_cam = "ทั้งหมด"
if view_mode == "เลือกสลับมุมกล้อง (Single View)":
    selected_cam = st.sidebar.selectbox("เลือกกล้องที่ต้องการดู", ["กล้องตัวที่ 1 (หน้าเคาน์เตอร์)", "กล้องตัวที่ 2 (ชั้นวางสินค้า)"])

# จำลองตารางคะแนนความเสี่ยงของแต่ละกล้อง
cam1_score = 0
cam2_score = 0

# 4. ส่วนแสดงฟีดวิดีโอ (Main Panel)
st.subheader("🖥️ หน้าจอหลักแสดงภาพจากกล้องวงจรปิด")

# สร้างพื้นที่ว่าง (Placeholder) ไว้สำหรับสลับการแสดงผลตามโหมดที่เลือก
video_area = st.empty()

# ส่วนแสดงสถานะและการแจ้งเตือนด้านล่างหน้าจอ
st.markdown("---")
col_stat1, col_stat2 = st.columns(2)

with col_stat1:
    st.markdown('<div class="status-card">🟢 <b>สถานะระบบ:</b> กำลังเฝ้าระวังปกติ</div>', unsafe_allow_html=True)
with col_stat2:
    alert_box = st.empty() # พื้นที่สำหรับแจ้งเตือนสีแดงเมื่อเจอขโมย

# 5. ลอจิกการเปิดกล้อง 2 ตัวพร้อมกัน
if run_system:
    # สำหรับการใช้งานจริง:
    # cap1 = cv2.VideoCapture(0) # กล้องตัวที่ 1 (Webcam เครื่อง)
    # cap2 = cv2.VideoCapture(1) # กล้องตัวที่ 2 (กล้องต่อแยกภายนอก)
    
    # 💡 ข้อแนะนำสำหรับการทดสอบ (ถ้ามีกล้องตัวเดียว): 
    # ให้กล้องตัวแรกเป็นกล้องจริง (0) และกล้องตัวที่สองเป็นไฟล์วิดีโอตัวอย่างแทนได้ครับ
    cap1 = cv2.VideoCapture(0)
    cap2 = cv2.VideoCapture("ใส่_path_ไฟล์วิดีโอทดสอบ.mp4") # หากไม่มีกล้องตัวที่ 2 ให้ระบุไฟล์วิดีโอแทน

    while cap1.isOpened() or cap2.isOpened():
        ret1, frame1 = cap1.read()
        ret2, frame2 = cap2.read()

        # สร้างเฟรมสีดำเปล่าๆ เผื่อกรณีกล้องตัวใดตัวหนึ่งเปิดไม่ได้ โค้ดจะได้ไม่พัง
        if not ret1:
            frame1 = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame1, "Camera 1 Disconnected", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        if not ret2:
            frame2 = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame2, "Camera 2 Disconnected", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # ส่งเฟรมไปประมวลผลด้วย YOLO (ถ้ากล้องทำงานปกติ)
        if ret1:
            res1 = model(frame1, verbose=False)
            frame1 = res1[0].plot()
            # เขียนข้อความกำกับหัวมุมภาพให้เหมือน CCTV
            cv2.putText(frame1, f"CAM 01 - FRONT COUNTER | {time.strftime('%H:%M:%S')}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        if ret2:
            res2 = model(frame2, verbose=False)
            frame2 = res2[0].plot()
            cv2.putText(frame2, f"CAM 02 - PRODUCT SHELF | {time.strftime('%H:%M:%S')}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # แปลงสี BGR เป็น RGB สำหรับ Streamlit
        frame1_rgb = cv2.cvtColor(frame1, cv2.COLOR_BGR2RGB)
        frame2_rgb = cv2.cvtColor(frame2, cv2.COLOR_BGR2RGB)

        # 6. อัปเดตหน้าจอตามโหมดการแสดงผลที่ผู้ใช้เลือกใน Sidebar
        with video_area.container():
            if view_mode == "ดูมุมกล้องรวม (Grid View)":
                # แบ่งหน้าจอซ้าย-ขวา แสดงผลพร้อมกัน
                cam_col1, cam_col2 = st.columns(2)
                with cam_col1:
                    st.image(frame1_rgb, use_container_width=True, caption="มุมมองกล้องที่ 1")
                with cam_col2:
                    st.image(frame2_rgb, use_container_width=True, caption="มุมมองกล้องที่ 2")
            
            elif view_mode == "เลือกสลับมุมกล้อง (Single View)":
                # แสดงผลเฉพาะกล้องเดี่ยวๆ ขนาดใหญ่
                if selected_cam == "กล้องตัวที่ 1 (หน้าเคาน์เตอร์)":
                    st.image(frame1_rgb, use_container_width=True, caption="กำลังขยาย: กล้องที่ 1")
                else:
                    st.image(frame2_rgb, use_container_width=True, caption="กำลังขยาย: กล้องที่ 2")

        # ตัวอย่างลอจิกจำลองการแจ้งเตือน (กรณีนำไปผสานกับโค้ดนับคะแนนความเสี่ยง logic.py)
        # สมมติว่ากล้องตัวที่ 2 ตรวจพบพฤติกรรมเสี่ยงเกินค่าที่กำหนด
        cam2_score = 6 # ตัวอย่างสมมติ
        if cam2_score >= 5:
            alert_box.markdown('<div class="alert-card">🚨 <b>แจ้งเตือนภัย:</b> ตรวจพบพฤติกรรมต้องสงสัยซ่อนสินค้าที่ [กล้องตัวที่ 2]</div>', unsafe_allow_html=True)
        else:
            alert_box.empty()

        # เพื่อป้องกันไม่ให้ CPU ทำงานหนักเกินไปในการรัน loop วิดีโอ
        time.sleep(0.01)

    cap1.release()
    cap2.release()
else:
    st.info("💡 กรุณากดปุ่ม 'เริ่มต้นทำงานระบบ (Start CCTV)' ที่แถบเมนูด้านข้างเพื่อเปิดใช้งานกล้อง")