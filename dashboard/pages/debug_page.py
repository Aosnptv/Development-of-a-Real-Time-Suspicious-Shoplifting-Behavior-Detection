import streamlit as st
import cv2
from core.app_state import AppState
from camera.camera_manager import CameraManager

def render_debug_page(camera_manager: CameraManager):
    st.title("🔧 System Diagnostics Terminal (Architecture Approved)")
    st.write("---")

    state = AppState()
    cam_id = 0
    cam_key = f"Camera_{cam_id}"
    
    # 📥 Dashboard ดึงข้อมูลจากคลังกลาง (AppState) เท่านั้น ไม่สร้างข้อมูลเอง
    cam_data = state.camera_pool.get(cam_key, {
        "online": False, "fps": 0.0, "resolution": "0 x 0", 
        "frame_count": 0, "dropped_frame": 0, "frame": None
    })
    sys_metrics = state.system_metrics

    # ==============================================================================
    # 🎥 VISUAL RENDER BLOCK
    # ==============================================================================
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📸 Pipeline Frame Consumer")
        # ดึงภาพจาก Buffer ที่ฝากไว้ใน AppState มาเรนเดอร์
        if cam_data["online"] and cam_data["frame"] is not None:
            # แปลงรหัสสีจากดิบ (BGR) เป็นสเปกหน้าเว็บ (RGB)
            rgb_frame = cv2.cvtColor(cam_data["frame"], cv2.COLOR_BGR2RGB)
            st.image(rgb_frame, channels="RGB", width="stretch")
        else:
            st.info("กล้องอยู่ในสถานะ OFFLINE หรือกำลังรอการเชื่อมต่อจาก Buffer...")

    with col2:
        st.subheader("📊 Data Stream Logs")
        status_text = "🟢 ONLINE" if cam_data["online"] else "🔴 OFFLINE"
        
        st.code(f"""
======================================
         CAMERA DIAGNOSTICS
======================================
Camera Status  : {status_text}
Frame Size     : {cam_data['resolution']}
Dynamic FPS    : {cam_data['fps']}
Total Frames   : {cam_data['frame_count']}
Dropped Frames : {cam_data['dropped_frame']}
======================================
        """, language="text")

        # ปุ่มกดสั่งการผ่านศูนย์ควบคุมระดับผู้จัดการ (Manager)
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("▶️ Start Pipeline", use_container_width=True):
                camera_manager.start_camera_pipeline(cam_id)
                st.rerun()
        with c2:
            if st.button("⏹️ Stop Pipeline", use_container_width=True):
                camera_manager.stop_camera_pipeline(cam_id)
                st.rerun()
        with c3:
            if st.button("🔄 Restart", use_container_width=True):
                camera_manager.restart_camera_pipeline(cam_id)
                st.rerun()

    st.write("---")
    
    # ==============================================================================
    # 🖥️ RESOURCE MONITOR BLOCK
    # ==============================================================================
    st.subheader("💻 Resource Usage Metrics")
    h1, h2, h3 = st.columns(3)
    h1.metric("CPU Usage", f"{sys_metrics['cpu']}%")
    h2.metric("RAM Usage", f"{sys_metrics['ram']}%")
    h3.metric("System Uptime", sys_metrics['uptime'])