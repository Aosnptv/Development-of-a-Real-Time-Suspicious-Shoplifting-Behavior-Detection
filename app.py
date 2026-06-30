import streamlit as st
import cv2
import pandas as pd
from database import init_db, get_all_incidents
from fsm_detector_multi import process_multi_camera, CAMERA_SOURCES

st.set_page_config(page_title="ระบบตรวจจับพฤติกรรมเสี่ยง Multi-Cam", layout="wide")
init_db()

st.title("🛒 Multi-Camera Shoplifting Detection System")
st.subheader("ระบบติดตามบุคคล (Tracking ID) และวิเคราะห์พฤติกรรมเสี่ยงแยกรายบุคคล")

col1, col2 = st.columns([2, 1])

with col1:
    st.header("📹 Live Camera Feed")
    # ตัวเลือกสลับกล้องที่ติดตั้งในระบบ
    selected_cam = st.selectbox("เลือกกล้องที่ต้องการมอนิเตอร์:", options=range(len(CAMERA_SOURCES)), format_func=lambda x: f"Camera {x+1}")
    run_system = st.checkbox("เปิดการใช้งานระบบตรวจจับ (Start)", value=False)
    st_frame = st.empty()

with col2:
    st.header("🚨 ประวัติการตรวจจับล่าสุด")
    refresh_btn = st.button("รีเฟรชประวัติ")
    history_placeholder = st.empty()

def update_history_table():
    data = get_all_incidents()
    if data:
        df = pd.DataFrame(data, columns=["ลำดับ", "วัน-เวลา", "คะแนนความเสี่ยง", "ที่อยู่ไฟล์ภาพ", "สถานะ"])
        history_placeholder.dataframe(df.drop(columns=["ที่อยู่ไฟล์ภาพ"]), use_container_width=True)
        if cv2.os.path.path.exists(data[0][3]):
            st.image(data[0][3], channels="BGR", use_container_width=True)

update_history_table()

if run_system:
    # เรียกทำงานตามไอดีกล้องที่ผู้ใช้เลือกบนหน้าเว็บ
    for frame in process_multi_camera(camera_index=CAMERA_SOURCES[selected_cam]):
        if not run_system:
            break
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        st_frame.image(frame_rgb, channels="RGB", use_container_width=True)
        if refresh_btn:
            update_history_table()