# app.py
import streamlit as st
import cv2
from ultralytics import YOLO
import numpy as np
import datetime
# นำเข้าไฟล์คำนวณคะแนนที่เราสร้างขึ้นมา
from behavior_analyzer import BehaviorAnalyzer 

st.set_page_config(page_title="CCTV Control Center", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <h2 style='text-align: left; font-weight: 600; font-family: sans-serif; margin-bottom: 5px;'>
        CCTV Monitor & Behavior Analysis System
    </h2>
    <div style='border-bottom: 2px solid #E2E8F0; margin-bottom: 20px;'></div>
""", unsafe_allow_html=True)

@st.cache_resource
def load_model():
    return YOLO('yolov8n.pt')

model = load_model()

# เรียกใช้งานคลาสคำนวณคะแนนพฤติกรรม (เก็บไว้ใน Cache เพื่อไม่ให้ระบบรีเซ็ตคะแนนทุกเฟรม)
@st.cache_resource
def init_analyzer():
    return BehaviorAnalyzer()

analyzer = init_analyzer()

CAM_SOURCES = {
    "CAM 01": {"source": 0, "name": "โซนเคาน์เตอร์ชำระเงิน"},
    "CAM 02": {"source": 1, "name": "โซนชั้นวางสินค้า A"},
    "CAM 03": {"source": 2, "name": "โซนชั้นวางสินค้า B"},
    "CAM 04": {"source": 3, "name": "โซนประตูทางเข้า-ออก"}
}

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "Grid 2x2"

# --- สร้างระบบหน่วยความจำเก็บบันทึกเหตุการณ์จริง (Dynamic Logs Stack) ---
if "system_logs" not in st.session_state:
    st.session_state.system_logs = ["[00:00:00] SYSTEM - เริ่มต้นระบบรักษาความปลอดภัย"]

st.sidebar.markdown("### แผงควบคุมระบบ")
run_system = st.sidebar.toggle("เปิดการทำงานของระบบ", value=False)

st.sidebar.markdown("---")
st.sidebar.markdown("#### มุมมองกล้อง")

is_grid_active = (st.session_state.view_mode == "Grid 2x2")
if st.sidebar.button("Grid 2x2", type="primary" if is_grid_active else "secondary", use_container_width=True):
    st.session_state.view_mode = "Grid 2x2"
    st.rerun()

c_col1, c_col2 = st.sidebar.columns(2)
with c_col1:
    if st.button("CAM 01", type="primary" if st.session_state.view_mode == "CAM 01" else "secondary", use_container_width=True):
        st.session_state.view_mode = "CAM 01"; st.rerun()
    if st.button("CAM 03", type="primary" if st.session_state.view_mode == "CAM 03" else "secondary", use_container_width=True):
        st.session_state.view_mode = "CAM 03"; st.rerun()
with c_col2:
    if st.button("CAM 02", type="primary" if st.session_state.view_mode == "CAM 02" else "secondary", use_container_width=True):
        st.session_state.view_mode = "CAM 02"; st.rerun()
    if st.button("CAM 04", type="primary" if st.session_state.view_mode == "CAM 04" else "secondary", use_container_width=True):
        st.session_state.view_mode = "CAM 04"; st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("#### บันทึกเหตุการณ์ระบบ (System Logs)")

# แสดงผล Log ที่เกิดขึ้นจริงจากหน่วยความจำ
log_display_text = "\n".join(st.session_state.system_logs[-6:]) # ดึง 6 เหตุการณ์ล่าสุดมาโชว์
st.sidebar.code(log_display_text, language="bash")

# --- ส่วนจัดโครงสร้างมอนิเตอร์ ---
view_mode = st.session_state.view_mode
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

# --- สถานะสแตนด์บาย (เมื่อปิดระบบ) ---
if not run_system:
    for cam_id in frame_places.keys():
        standby_frame = np.ones((270, 480, 3), dtype=np.uint8) * 235
        cv2.putText(standby_frame, "SYSTEM STANDBY", (140, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (160, 174, 192), 2)
        standby_rgb = cv2.cvtColor(standby_frame, cv2.COLOR_BGR2RGB)
        frame_places[cam_id].image(standby_rgb, channels="RGB", use_container_width=True)
        score_places[cam_id].caption("สถานะ: ปิดการทำงาน")

# --- สถานะรันกล้องจริงทำงาน ---
else:
    caps = {}
    for cam_id, config in CAM_SOURCES.items():
        caps[cam_id] = cv2.VideoCapture(config["source"])

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
                frame_out = cv2.resize(frame_out, (480, 270))
                
                # 🔥 [จุดเชื่อมต่อระบบคำนวณคะแนนพฤทธิกรรม]
                # ส่งผลลัพธ์ของ YOLOv8 ไปคำนวณที่ไฟล์ behavior_analyzer.py
                current_score, log_message = analyzer.analyze_frame_objects(cam_id, results)
                
                # จัดกลุ่มคำแสดงระดับความเสี่ยงตามคะแนนที่ส่งกลับมา
                if current_score >= 5:
                    risk_text = f"🚨 ดัชนีความเสี่ยงพฤติกรรม: {current_score} / 5 (อันตราย/เสี่ยงขโมย)"
                elif current_score >= 3:
                    risk_text = f"⚠️ ดัชนีความเสี่ยงพฤติกรรม: {current_score} / 5 (ควรเฝ้าระวัง)"
                else:
                    risk_text = f"ดัชนีความเสี่ยงพฤติกรรม: {current_score} / 5 (ปกติ)"

                # หากไฟล์คำนวณส่ง Log ตัวใหม่มา ให้ประทับเวลาและบันทึกลงแถบด้านซ้ายทันทีแบบอัตโนมัติ
                if log_message:
                    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                    st.session_state.system_logs.append(f"[{timestamp}] {log_message}")

            frame_rgb = cv2.cvtColor(frame_out, cv2.COLOR_BGR2RGB)

            if cam_id in frame_places:
                frame_places[cam_id].image(frame_rgb, channels="RGB", use_container_width=True)
                score_places[cam_id].caption(risk_text)

        if not run_system:
            break

    for cap in caps.values():
        cap.release()