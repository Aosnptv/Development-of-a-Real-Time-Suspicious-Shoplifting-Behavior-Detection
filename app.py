import streamlit as st
import cv2
import pandas as pd
import os
import time
from database import init_db, get_all_incidents
from fsm_detector_multi import CAMERA_SOURCES, CameraStream, process_frame_pipeline

st.set_page_config(page_title="ระบบควบคุมกล้องตรวจจับพฤติกรรม", layout="wide")
init_db()

st.title("📹 ระบบควบคุมพื้นที่ตรวจจับพฤติกรรมเสี่ยง (Multi-Camera Stable Grid)")
st.write("ตีกรอบและกำหนดพื้นที่ขอบเขตสินค้าแยกกล้องได้อย่างอิสระ แนะนำให้ตั้งพิกัดสไลเดอร์ให้เรียบร้อยก่อนกดเริ่มการทำงานระบบ")

st.sidebar.header("⚙️ ตั้งค่าระบบกล้อง")
selected_cameras = st.sidebar.multiselect(
    "เลือกกล้องที่ต้องการมอนิเตอร์ในระบบ:",
    options=list(CAMERA_SOURCES.keys()),
    default=list(CAMERA_SOURCES.keys())
)

camera_zones = {}
for cam_name in selected_cameras:
    st.sidebar.markdown(f"---")
    st.sidebar.subheader(f"🎯 พิกัดโซนของ: {cam_name}")
    x_range = st.sidebar.slider(f"แกนนอน (ซ้าย-ขวา) - {cam_name}", 0, 640, (50, 250), key=f"x_{cam_name}")
    y_range = st.sidebar.slider(f"แกนตั้ง (บน-ล่าง) - {cam_name}", 0, 480, (200, 400), key=f"y_{cam_name}")
    camera_zones[cam_name] = [x_range[0], y_range[0], x_range[1], y_range[1]]

st.sidebar.markdown("---")
run_system = st.sidebar.checkbox("▶️ เริ่มการทำงานของระบบ (Start System)", value=False)

st.sidebar.header("🚨 หลักฐานภาพถ่ายล่าสุด")
image_slot = st.sidebar.empty()
history_slot = st.sidebar.empty()

def render_sidebar_data():
    data = get_all_incidents()
    if data:
        df = pd.DataFrame(data, columns=["ลำดับ", "วัน-เวลา", "คะแนน", "ไฟล์ภาพ", "status"])
        history_slot.dataframe(df.drop(columns=["ไฟล์ภาพ", "status"]), use_container_width=True)
        latest_img = data[0][3]
        if latest_img and os.path.exists(latest_img):
            image_slot.image(latest_img, caption="ตรวจพบเหตุการณ์ล่าสุด", use_container_width=True)

render_sidebar_data()

# --- ส่วนของการจัดสรรหน้าจอกล้องหลายตัว (Multi-Cam Grid Rendering) ---
if run_system and len(selected_cameras) > 0:
    streams = {}
    for cam_name in selected_cameras:
        streams[cam_name] = CameraStream(CAMERA_SOURCES[cam_name])

    # ปรับสล็อต Grid หน้าจอตามจำนวนกล้องที่ผู้ใช้เลือกให้แสดงผล
    cols = st.columns(len(selected_cameras)) if len(selected_cameras) > 1 else [st.empty()]
    ui_slots = {cam_name: cols[idx].empty() for idx, cam_name in enumerate(selected_cameras)}

    last_known_incident_count = len(get_all_incidents())

    try:
        while run_system:
            for cam_name in selected_cameras:
                if cam_name in streams:
                    ret, frame = streams[cam_name].read()
                    if ret and frame is not None:
                        # นำพิกัดล่าสุดที่ผ่านการสไลด์จากตัวแปร camera_zones ไปประมวลผล
                        current_zone = camera_zones[cam_name]
                        processed_frame = process_frame_pipeline(frame.copy(), cam_name, current_zone)
                        
                        frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                        ui_slots[cam_name].image(frame_rgb, caption=cam_name, use_container_width=True)
            
            # ตรวจเช็กการเซฟภาพแจ้งเตือนแบบเรียลไทม์
            current_count = len(get_all_incidents())
            if current_count > last_known_incident_count:
                render_sidebar_data()
                last_known_incident_count = current_count
                
            time.sleep(0.01) # พักลูปสั้นๆ เพื่อให้ CPU ไม่ทำงานหนักเกินไปและช่วยให้การกดปิดลูปตอบสนองได้ดีขึ้น
    finally:
        for cam_name in list(streams.keys()):
            streams[cam_name].stop()
            
elif len(selected_cameras) == 0:
    st.info("💡 กรุณาคลิกเลือกกล้องอย่างน้อย 1 ตัวที่แถบเมนูด้านซ้ายเพื่อเริ่มต้น")
else:
    st.info("⏸️ ระบบปิดอยู่ กรุณาปรับตั้งค่าพิกัด PRODUCT ZONE ด้านซ้ายให้เรียบร้อย แล้วกด 'เริ่มการทำงานของระบบ'")