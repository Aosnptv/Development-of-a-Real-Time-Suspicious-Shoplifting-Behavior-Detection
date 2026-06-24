import streamlit as st
import cv2
from ultralytics import YOLO
import numpy as np

# ตั้งค่าหน้าจอแบบกว้าง (Wide)
st.set_page_config(
    page_title="CCTV Control Center", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# ส่วนหัวระบบ (ตัวหนังสือจะเปลี่ยนสีอัตโนมัติตามโหมดมืด/สว่าง)
st.markdown("""
    <h2 style='text-align: left; font-weight: 600; font-family: sans-serif; margin-bottom: 5px;'>
        CCTV Monitor & Behavior Analysis System
    </h2>
    <div style='border-bottom: 2px solid #E2E8F0; margin-bottom: 20px;'></div>
""", unsafe_allow_html=True)

# โหลดโมเดลสำหรับประมวลผล AI
@st.cache_resource
def load_model():
    return YOLO('yolov8n.pt')

model = load_model()

# รายการกล้องวงจรปิดในระบบ
CAM_SOURCES = {
    "CAM 01": {"source": 0, "name": "โซนเคาน์เตอร์ชำระเงิน"},
    "CAM 02": {"source": 1, "name": "โซนชั้นวางสินค้า A"},
    "CAM 03": {"source": 2, "name": "โซนชั้นวางสินค้า B"},
    "CAM 04": {"source": 3, "name": "โซนประตูทางเข้า-ออก"}
}

# กำหนดสถานะเริ่มต้นให้กับมุมมองกล้อง
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "Grid 2x2"

# --- แถบควบคุมด้านซ้าย (Sidebar) ---
st.sidebar.markdown("### แผงควบคุมระบบ")

# สวิตช์หลักสำหรับเปิดทำงานระบบ
run_system = st.sidebar.toggle("เปิดการทำงานของระบบ", value=False)

st.sidebar.markdown("---")
st.sidebar.markdown("#### มุมมองกล้อง")

# 1. ปุ่มสำหรับดูภาพรวม 4 กล้องพร้อมกัน (เต็มความกว้างของแถบข้าง)
is_grid_active = (st.session_state.view_mode == "Grid 2x2")
if st.sidebar.button("Grid 2x2", type="primary" if is_grid_active else "secondary", use_container_width=True):
    st.session_state.view_mode = "Grid 2x2"
    st.rerun()

# 2. ย่อขนาดปุ่มเลือกกล้องเดี่ยวโดยแบ่งเป็น 2 คอลัมน์เล็กๆ ซ้าย-ขวา เพื่อประหยัดพื้นที่
c_col1, c_col2 = st.sidebar.columns(2)

with c_col1:
    if st.button("CAM 01", type="primary" if st.session_state.view_mode == "CAM 01" else "secondary", use_container_width=True):
        st.session_state.view_mode = "CAM 01"
        st.rerun()
    if st.button("CAM 03", type="primary" if st.session_state.view_mode == "CAM 03" else "secondary", use_container_width=True):
        st.session_state.view_mode = "CAM 03"
        st.rerun()

with c_col2:
    if st.button("CAM 02", type="primary" if st.session_state.view_mode == "CAM 02" else "secondary", use_container_width=True):
        st.session_state.view_mode = "CAM 02"
        st.rerun()
    if st.button("CAM 04", type="primary" if st.session_state.view_mode == "CAM 04" else "secondary", use_container_width=True):
        st.session_state.view_mode = "CAM 04"
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("#### บันทึกเหตุการณ์ระบบ (System Logs)")

# ขยายพื้นที่แสดง Log ให้กว้าง เต็มตา และเพิ่มข้อมูลจำลองให้ดูเป็นทางการขึ้น
log_text = (
    "[14:22:10] SYSTEM - Connected to 4 Cameras\n"
    "[14:22:12] CAM 01 - Suspicious Behavior [ALERT]\n"
    "[14:22:15] CAM 02 - Normal activity detected\n"
    "[14:24:02] CAM 01 - Score updated: 3/5\n"
    "[14:25:11] CAM 03 - Normal activity detected"
)
st.sidebar.code(log_text, language="bash")


# --- พื้นที่แสดงผลมอนิเตอร์หลัก (Main Area) ---
view_mode = st.session_state.view_mode

if run_system:
    caps = {}
    for cam_id, config in CAM_SOURCES.items():
        caps[cam_id] = cv2.VideoCapture(config["source"])

    frame_places = {}
    score_places = {}

    if view_mode == "Grid 2x2":
        row1_col1, row1_col2 = st.columns(2)
        row2_col1, row2_col2 = st.columns(2)
        
        cols = [row1_col1, row1_col2, row2_col1, row2_col2]
        for idx, cam_id in enumerate(CAM_SOURCES.keys()):
            with cols[idx]:
                st.markdown(f"**{cam_id}: {CAM_SOURCES[cam_id]['name']}**")
                frame_places[cam_id] = st.empty()
                score_places[cam_id] = st.empty()
    else:
        st.markdown(f"### มุมมองขยาย: {view_mode} ({CAM_SOURCES[view_mode]['name']})")
        frame_places[view_mode] = st.empty()
        score_places[view_mode] = st.empty()


    # ลูปทำงานหลัก
    while True:
        for cam_id, cap in caps.items():
            if view_mode != "Grid 2x2" and cam_id != view_mode:
                continue

            success, frame = cap.read()

            if not success:
                frame_out = np.ones((270, 480, 3), dtype=np.uint8) * 230
                cv2.putText(frame_out, f"{cam_id} OFFLINE", (140, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (148, 163, 184), 2)
                risk_text = "สถานะ: ไม่สามารถเชื่อมต่อได้"
            else:
                results = model(frame)
                frame_out = results[0].plot()
                frame_out = cv2.resize(frame_out, (480, 270)) # บีบสัดส่วนป้องกันการเกิด Scroll bar
                risk_text = "ดัชนีความเสี่ยงพฤติกรรม: 0 / 5 (ปกติ)"

            frame_rgb = cv2.cvtColor(frame_out, cv2.COLOR_BGR2RGB)

            if cam_id in frame_places:
                frame_places[cam_id].image(frame_rgb, channels="RGB", use_container_width=True)
                score_places[cam_id].caption(risk_text)

        if not run_system:
            break

    for cap in caps.values():
        cap.release()

else:
    st.markdown("ระบบพร้อมใช้งาน กรุณากดเปิดสวิตช์ที่แผงควบคุมด้านซ้ายเพื่อเริ่มต้นมอนิเตอร์กล้องวงจรปิด")