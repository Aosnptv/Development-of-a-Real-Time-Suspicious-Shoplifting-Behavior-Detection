import streamlit as st
import cv2
from core.app_state import AppState
from camera.camera_manager import CameraManager
from database.database_service import DatabaseService

state = AppState()
cam_manager = CameraManager()
db = DatabaseService()

def render_camera_management_page():
    st.markdown("## 🎥 Camera Pipeline Control Center (Sprint 4.0)")
    
    # ส่วนที่ 1: การ์ดสตรีมภาพสดและค่าสเปกฮาร์ดแวร์จริง
    st.markdown("### Live Feeds")
    cameras_in_pool = state.camera_pool
    
    if not cameras_in_pool:
        st.info("No active camera streams detected in AppState. Ensure database has registered devices.")
    else:
        # วาง Layout จอแบบ 2 คอลัมน์ขนาน
        cols = st.columns(2)
        for idx, (cam_name, cam_info) in enumerate(cameras_in_pool.items()):
            col = cols[idx % 2]
            with col:
                # 🟢 บ่งชี้สถานะ Online/Offline
                status_indicator = "🟢 ONLINE" if cam_info["online"] else "🔴 OFFLINE"
                
                # 📊 แสดงผลความละเอียด (Resolution) และความเร็วภาพจริง (FPS) บนหัวจอ
                st.markdown(f"#### {cam_name} | {status_indicator}")
                st.caption(f"⚙️ Resolution: {cam_info['resolution']} | ⚡ Actual FPS: {cam_info['fps']}")
                
                frame = cam_info.get("frame")
                if frame is not None and cam_info["online"]:
                    # 🔃 แปลงรหัสสีภาพดิบจาก OpenCV (BGR) เป็นสเปกหน้าจอเบราว์เซอร์ (RGB)
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    st.image(frame_rgb, use_container_width=True)
                else:
                    # กรณีกล้องถูกปิด หรือสตรีมยังหลุด/บัฟเฟอร์อยู่
                    st.error("Video stream is currently stopped or unreachable.")
                    
                # ปุ่มควบคุมเฉพาะรายกล้อง
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    if st.button(f"Restart {cam_name}", key=f"rst_{cam_name}"):
                        cam_manager.restart_camera(cam_name)
                        st.toast(f"Manually restarted thread for {cam_name}!")
                        
    st.write("---")
    
    # ส่วนที่ 2: เมนูบริหารจัดการ เพิ่ม/ลบ และปรับสถานะกล้องใน Database
    st.markdown("### ⚙️ Camera Fleet Configuration")
    
    # ดึงตารางกล้องจากฐานข้อมูล SQLite ขึ้นมาแสดง
    cam_list_db = db.get_all_cameras()
    
    # แสดงตารางบอกสถานะภาพรวมของกล้องทั้งหมด
    st.markdown("**Registered Devices in Database:**")
    st.dataframe(
        cam_list_db,
        use_container_width=True,
        column_config={
            "id": "ID", "name": "Camera Name", "source": "Input Source (Webcam Index / RTSP URL)",
            "status": "DB Status", "resolution": "Resolution", "fps": "FPS Limit"
        }
    )
    
    # ฟอร์มเพิ่มกล้องตัวใหม่เข้าสู่ระบบ (เช่น เสียบ USB Webcam ตัวที่สอง เพิ่มเลข Source เป็น 1)
    with st.expander("➕ Register New Camera to System"):
        with st.form("add_camera_form", clear_on_submit=True):
            new_name = st.text_input("Camera Name", placeholder="e.g., Warehouse Entrance")
            new_source = st.text_input("Source Type / Index", placeholder="0 for internal webcam, or enter RTSP path")
            submit_btn = st.form_submit_button("Save to Database")
            
            if submit_btn and new_name and new_source:
                db.add_camera(new_name, new_source)
                st.success(f"Successfully added '{new_name}' to system! Restart app to deploy thread.")