import streamlit as st
import cv2
import pandas as pd
import os
import time
from database import init_db, get_all_incidents
from fsm_detector_multi import CAMERA_SOURCES, CameraStream, process_frame_pipeline

st.set_page_config(page_title="ระบบตรวจจับขโมยอัตโนมัติ", layout="wide")
init_db()

st.title("🛒 ระบบตรวจจับพฤติกรรมเส่อนสินค้าอัจฉริยะ (Auto-Detection Mode)")
st.write("โมเดลจะทำการค้นหาตำแหน่งของ 'โต๊ะ/ชั้นวางของ' และเพิ่มระบบนับเลขเฟรมสะสมที่ขวาล่างของมุมกล้อง")

# --- แถบเครื่องมือด้านซ้าย (Sidebar) ---
st.sidebar.header("⚙️ จัดการระบบกล้อง")
selected_cameras = st.sidebar.multiselect(
    "เลือกกล้องวงจรปิดที่ต้องการมอนิเตอร์:",
    options=list(CAMERA_SOURCES.keys()),
    default=list(CAMERA_SOURCES.keys())
)

st.sidebar.markdown("---")
run_system = st.sidebar.checkbox("▶️ เริ่มการทำงานของระบบ (Start System)", value=False)

st.sidebar.header("🚨 หลักฐานภาพถ่ายล่าสุด")
image_slot = st.sidebar.empty()
history_slot = st.sidebar.empty()

def render_sidebar_data():
    data = get_all_incidents()
    if data:
        # อัปเดตใช้ width='stretch' ในตารางดาต้าเฟรม
        df = pd.DataFrame(data, columns=["ลำดับ", "วัน-เวลา", "คะแนน", "ไฟล์ภาพ", "status"])
        history_slot.dataframe(df.drop(columns=["ไฟล์ภาพ", "status"]), width='stretch')
        latest_img = data[0][3]
        if latest_img and os.path.exists(latest_img):
            # อัปเดตใช้ width='stretch' ในการแสดงผลรูปภาพหลักฐาน
            image_slot.image(latest_img, caption="หลักฐานจากระบบอัตโนมัติ", width='stretch')

render_sidebar_data()

# --- ส่วนจัดแสดงวิดีโอกล้องหลายตัวพร้อมกัน ---
if run_system and len(selected_cameras) > 0:
    streams = {}
    for cam_name in selected_cameras:
        streams[cam_name] = CameraStream(CAMERA_SOURCES[cam_name])

    cols = st.columns(len(selected_cameras)) if len(selected_cameras) > 1 else [st.empty()]
    ui_slots = {cam_name: cols[idx].empty() for idx, cam_name in enumerate(selected_cameras)}

    last_known_incident_count = len(get_all_incidents())

    try:
        while run_system:
            for cam_name in selected_cameras:
                if cam_name in streams:
                    ret, frame, frame_num = streams[cam_name].read()
                    if ret and frame is not None:
                        processed_frame = process_frame_pipeline(frame.copy(), cam_name, frame_num)
                        frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                        # อัปเดตใช้ width='stretch' ในส่วนการแสดงผลภาพสดจากวิดีโอกล้อง
                        ui_slots[cam_name].image(frame_rgb, caption=cam_name, width='stretch')
            
            current_count = len(get_all_incidents())
            if current_count > last_known_incident_count:
                render_sidebar_data()
                last_known_incident_count = current_count
                
            time.sleep(0.01)
    finally:
        for cam_name in list(streams.keys()):
            streams[cam_name].stop()
            
elif len(selected_cameras) == 0:
    st.info("💡 กรุณาเลือกกล้องวงจรปิดที่ต้องการดูในแผงควบคุมซ้ายมือ")
else:
    st.info("⏸️ ระบบจดจำอัตโนมัติพร้อมใช้งาน ติ๊กถูกที่ช่อง 'เริ่มการทำงานของระบบ' เพื่อเปิดการคำนวณแบบ Multi-Cam")