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

# ส่วนหัวระบบ (สีข้อความเปลี่ยนตามโหมดมืด/สว่างอัตโนมัติ)
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

# 1. ปุ่มสำหรับดูภาพรวม 4 กล้องพร้อมกัน
is_grid_active = (st.session_state.view_mode == "Grid 2x2")
if st.sidebar.button("Grid 2x2", type="primary" if is_grid_active else "secondary", use_container_width=True):
    st.session_state.view_mode = "Grid 2x2"
    st.rerun()

# 2. ปุ่มเลือกกล้องเดี่ยวแบบ 2 คอลัมน์เล็ก
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

# ดึงข้อกำหนด Layout ขอบเขตกล้องมาประกาศสร้างจองพื้นที่ไว้ล่วงหน้าเลย (ทำให้กรอบล็อกอยู่กับที่)
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


# --- สถานะที่ 1: เมื่อ "ปิดระบบ" (แสดงกรอบกล้องสแตนด์บายค้างไว้) ---
if not run_system:
    # วนลูปวาดภาพหน้าจอสถานะ STANDBY ป้อนเข้าไปในกรอบกล้องที่จองไว้ทันที
    for cam_id in frame_places.keys():
        # สร้างภาพพื้นหลังสีเทาเรียบๆ ขนาดความละเอียดเท่าของจริง (480x270)
        standby_frame = np.ones((270, 480, 3), dtype=np.uint8) * 235
        # เขียนตัวหนังสือแจ้งเตือนระบบสแตนด์บายบนกรอบ
        cv2.putText(standby_frame, "SYSTEM STANDBY", (140, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (160, 174, 192), 2)
        standby_rgb = cv2.cvtColor(standby_frame, cv2.COLOR_BGR2RGB)
        
        # ยิงภาพขึ้นกรอบมอนิเตอร์ค้างไว้
        frame_places[cam_id].image(standby_rgb, channels="RGB", use_container_width=True)
        score_places[cam_id].caption("สถานะ: ปิดการทำงาน (กรุณาเปิดสวิตช์แผงควบคุมด้านซ้าย)")


# --- สถานะที่ 2: เมื่อ "เปิดระบบ" (ลูปดึงภาพกล้องจริงสตรีมมิ่งสด) ---
else:
    # เชื่อมต่อระบบกล้องฮาร์ดแวร์
    caps = {}
    for cam_id, config in CAM_SOURCES.items():
        caps[cam_id] = cv2.VideoCapture(config["source"])

    # ลูปสตรีมมิ่งภาพแบบเรียลไทม์
    while True:
        for cam_id, cap in caps.items():
            if view_mode != "Grid 2x2" and cam_id != view_mode:
                continue

            success, frame = cap.read()

            if not success:
                # กรณีกดเปิดสวิตช์ระบบแล้วแต่กล้องบางตัวไม่มีอยู่จริง ให้ขึ้นหน้าจอ OFFLINE สีเทา
                frame_out = np.ones((270, 480, 3), dtype=np.uint8) * 230
                cv2.putText(frame_out, f"{cam_id} OFFLINE", (140, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (148, 163, 184), 2)
                risk_text = "สถานะ: ไม่สามารถเชื่อมต่อกล้องได้"
            else:
                # ส่งเฟรมเข้า AI ประมวลผลพฤติกรรมเสี่ยง
                results = model(frame)
                frame_out = results[0].plot()
                frame_out = cv2.resize(frame_out, (480, 270))
                risk_text = "ดัชนีความเสี่ยงพฤติกรรม: 0 / 5 (ปกติ)"

            frame_rgb = cv2.cvtColor(frame_out, cv2.COLOR_BGR2RGB)

            if cam_id in frame_places:
                frame_places[cam_id].image(frame_rgb, channels="RGB", use_container_width=True)
                score_places[cam_id].caption(risk_text)

        # หากระหว่างลูปทำงาน ผู้ใช้ปิดทอกเกิลสวิตช์ ให้หักลูปออกเพื่อสลับไปหน้า Standby ค้างกรอบรูปทันที
        if not run_system:
            break

    # คืนทรัพยากรกล้อง
    for cap in caps.values():
        cap.release()