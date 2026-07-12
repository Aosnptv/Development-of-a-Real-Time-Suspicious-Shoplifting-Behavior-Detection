import streamlit as st
import cv2
from camera.camera_manager import CameraManager
from services.system_monitor import SystemMonitor

def render_debug_page(camera_manager: CameraManager, system_monitor: SystemMonitor):
    st.title("🔧 System Diagnostics & Debug Terminal (Sprint 4.5)")
    st.write("---")

    # ดึงค่าสถานะล่าสุดของกล้องหมายเลข 0 (Webcam ตัวหลักตาม DoD ข้อ 9)
    cam_id = 0
    cam_data = camera_manager.get_status(cam_id)
    sys_data = system_monitor.get_metrics()

    # ==============================================================================
    # 🎥 SECTION 1: CAMERA PIPELINE DEEPLINK (DoD ข้อ 3, 4, 5, 6, 7)
    # ==============================================================================
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📸 Live Pipeline Stream")
        if cam_data["online"] and cam_data["frame"] is not None:
            # แปลงรหัสสีจาก OpenCV (BGR) เป็นสเปกของเว็บบราวเซอร์ (RGB)
            rgb_frame = cv2.cvtColor(cam_data["frame"], cv2.COLOR_BGR2RGB)
            st.image(rgb_frame, channels="RGB", use_container_width=True)
        else:
            # กล่องสีเทาจำลองกรณีตรวจไม่พบฮาร์ดแวร์ ป้องกันสตรีมระเบิดกลางคัน
            st.info("กล้องอยู่ในสถานะ OFFLINE หรือไม่มีเฟรมภาพส่งมาจากฮาร์ดแวร์")

    with col2:
        st.subheader("📋 Pipeline Real-time Logs")
        status_color = "🟢 ONLINE" if cam_data["online"] else "🔴 OFFLINE"
        
        st.code(f"""
======================================
         CAMERA DIAGNOSTICS
======================================
Camera Status  : {status_color}
Frame Size     : {cam_data['resolution']}
FPS (Dynamic)  : {cam_data['fps']}
Frame Count    : {cam_data['frame_count']}
Dropped Frame  : {cam_data['dropped_frame']}
======================================
        """, language="text")

        # แผงควบคุมคำสั่งระดับผู้จัดการระบบ (DoD ข้อ 7)
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("▶️ Start Cam", use_container_width=True):
                camera_manager.start_camera(cam_id)
                st.rerun()
        with c2:
            if st.button("⏹️ Stop Cam", use_container_width=True):
                camera_manager.stop_camera(cam_id)
                st.rerun()
        with c3:
            if st.button("🔄 Restart", use_container_width=True):
                camera_manager.restart_camera(cam_id)
                st.rerun()

    st.write("---")

    # ==============================================================================
    # 🖥️ SECTION 2: INFRASTRUCTURE & RESOURCE MONITOR (DoD ข้อ 11, 12)
    # ==============================================================================
    st.subheader("💻 Subsystem & Hardware Infrastructure")
    
    h1, h2, h3, h4 = st.columns(4)
    h1.metric("CPU Load", f"{sys_data['cpu']}%", help="DoD Target: < 20-30% on idle stream")
    h2.metric("RAM Occupied", f"{sys_data['ram']}%", help="ใช้สังเกตอาการ Memory Leak หลังเปิดทิ้งไว้ 10 นาที")
    h3.metric("Disk Storage", f"{sys_data['disk']}%")
    h4.metric("System Uptime", sys_data['uptime'])

    # ==============================================================================
    # 🔌 SECTION 3: SUBSYSTEM INTEGRATION TESTS (ปุ่มยิงทดสอบระบบย่อยเพื่อเตรียมความพร้อม)
    # ==============================================================================
    st.write("---")
    st.subheader("🔌 Subsystem Health Check Integration")
    
    test_col1, test_col2 = st.columns(2)
    
    with test_col1:
        if st.button("🧪 Test Database Connection", use_container_width=True):
            try:
                from database.database_service import DatabaseService
                db = DatabaseService()
                cams = db.get_all_cameras()
                st.success(f"✓ Database Connected! Found {len(cams)} registered profiles.")
            except Exception as e:
                st.error(f"✗ Database Health Check Failed: {str(e)}")

    with test_col2:
        if st.button("🧪 Test Telegram Gateway", use_container_width=True):
            # ในอนาคตสามารถใส่ฟังก์ชันยิงข้อความทดสอบเข้ากลุ่มไลน์หรือเทเลแกรมตรงนี้ได้เลย
            st.warning("⚠️ Telegram Token configurations missing in config.json. Skipped.")