import streamlit as st
import cv2
import pandas as pd
import os
import time
from database import init_db, get_all_incidents, get_dashboard_stats
from fsm_detector_multi import CAMERA_SOURCES, CameraStream, process_frame_pipeline

# ตั้งค่าหน้าเว็บให้ขยายเต็มจอเพื่อความสวยงามในหน้าเดียว
st.set_page_config(page_title="Retail Security Dashboard", layout="wide")
init_db()

# ส่วนหัวโปรแกรมแบบเป็นทางการ
st.subheader("Shoplifting Detection and Sequential Behavior Analysis Dashboard")

# แบ่งหน้าจอออกเป็น 2 คอลัมน์หลักซ้าย-ขวา (คอลัมน์ซ้ายสตรีมกล้อง / คอลัมน์ขวาวิเคราะห์สถิติและฐานข้อมูล)
left_main_col, right_main_col = st.columns([1, 1])

# --- ฝั่งซ้าย: ฟีดวิดีโอคู่ขนานจากระบบกล้องวงจรปิด ---
with left_main_col:
    st.write("Real-time Video Stream Input")
    
    # เมนูควบคุมกล้องขนาดกะทัดรัด
    ctrl_col1, ctrl_col2 = st.columns(2)
    with ctrl_col1:
        selected_cameras = st.multiselect(
            "Select Cameras:",
            options=list(CAMERA_SOURCES.keys()),
            default=list(CAMERA_SOURCES.keys()),
            label_visibility="collapsed"
        )
    with ctrl_col2:
        run_system = st.checkbox("Execute AI Pipeline", value=False)
        
    st.markdown("---")

    if run_system and len(selected_cameras) > 0:
        streams = {}
        for cam_name in selected_cameras:
            streams[cam_name] = CameraStream(CAMERA_SOURCES[cam_name])

        # จัดภาพกล้องให้ซ้อนกันแนวดิ่ง เพื่อไม่ให้บีบหน้าจอและอยู่ในขอบเขตสายตาโดยไม่ต้องเลื่อน
        ui_slots = {}
        for cam_name in selected_cameras:
            ui_slots[cam_name] = st.empty()

        last_known_count = len(get_all_incidents())

        try:
            while run_system:
                for cam_name in selected_cameras:
                    if cam_name in streams:
                        ret, frame, frame_num = streams[cam_name].read()
                        if ret and frame is not None:
                            processed_frame = process_frame_pipeline(frame.copy(), cam_name, frame_num)
                            frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                            ui_slots[cam_name].image(frame_rgb, caption=cam_name, width='stretch')
                
                current_count = len(get_all_incidents())
                if current_count > last_known_count:
                    st.rerun()
                
                time.sleep(0.01)
        finally:
            for cam_name in list(streams.keys()):
                streams[cam_name].stop()
    else:
        st.info("System Standby: Please toggle 'Execute AI Pipeline' to view real-time streams.")

# --- ฝั่งขวา: สถิติรวมประมวลผล KPI, แผนภูมิความถี่ และตารางเหตุการณ์ย้อนหลัง ---
with right_main_col:
    st.write("Analytical Statistics and Logs")
    
    # 1. แสดงผล KPI ข้อมูลสรุปตัวเลขแบบทางการ
    total_incidents, today_incidents = get_dashboard_stats()
    kpi_1, kpi_2, kpi_3 = st.columns(3)
    kpi_1.metric(label="Total Logged Incidents", value=f"{total_incidents} Cases")
    kpi_2.metric(label="Today's Occurrences", value=f"{today_incidents} Cases")
    kpi_3.metric(label="System Status", value="Online")
    
    st.markdown("---")
    
    # 2. แผนภูมิแท่งสรุปสัดส่วนระดับความเสี่ยงเพื่อวิเคราะห์ระดับโครงงาน (ปรับความสูงให้เตี้ยลงเพื่อความกระชับ)
    st.write("Risk Score Distribution Profile")
    all_data = get_all_incidents()
    if all_data:
        df_chart = pd.DataFrame(all_data, columns=["ID", "Timestamp", "Score", "Path", "Status"])
        score_counts = df_chart["Score"].value_counts().reset_index()
        score_counts.columns = ["Risk Score", "Occurrences"]
        st.bar_chart(score_counts.set_index("Risk Score"), height=140)
    else:
        st.caption("No statistical data available.")
        
    st.markdown("---")
    
    # 3. ตารางประวัติ Log ข้อมูล บีบแถวให้แสดงผลแบบสั้นกระชับ
    st.write("Incident Log Database Table")
    if all_data:
        df_table = pd.DataFrame(all_data, columns=["ID", "Timestamp", "Risk Score (FSM)", "Image Path", "Notification Status"])
        st.dataframe(df_table.drop(columns=["Image Path"]), height=160, width='stretch')
        
        # 4. แสดงภาพหลักฐานล่าสุดขนาดพอเหมาะด้านล่างสุดของฝั่งขวา
        latest_img_path = all_data[0][3]
        if latest_img_path and os.path.exists(latest_img_path):
            st.write("Latest Suspicious Snapshot Proof")
            st.image(latest_img_path, width='stretch')
    else:
        st.caption("Database empty. No exceptions detected.")