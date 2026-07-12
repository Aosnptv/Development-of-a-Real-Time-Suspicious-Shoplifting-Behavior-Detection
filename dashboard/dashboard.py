import streamlit as st
import time
from core.app_state import AppState
from services.system_monitor import SystemMonitor
from database.database_service import DatabaseService
from camera.camera_manager import CameraManager
from dashboard.components import render_top_status_bar, render_bottom_subsystem_bar
from dashboard.metric_card import render_kpi_section
from dashboard.status_card import render_system_status_and_logs

# Initialize คลาสควบคุมหลังบ้าน
monitor = SystemMonitor()
db = DatabaseService()
cam_manager = CameraManager()
state = AppState()

def init_services():
    """โหลดรายชื่อกล้องจาก DB เข้ามาในระบบ Threading ครั้งแรกครั้งเดียว"""
    if not hasattr(st.session_state, "camera_initialized"):
        # ดึงรายชื่อกล้องจากตาราง SQLite
        camera_list = db.get_all_cameras()
        # ส่งให้ Manager สั่งเปิด Thread ประมวลผลแยกรายกล้องเบื้องหลัง
        cam_manager.register_and_start_cameras(camera_list)
        st.session_state.camera_initialized = True

def refresh_container():
    """Loop รีเฟรชข้อมูลสถานะและเฟรมภาพสดเข้าสู่ State และ UI"""
    # 1. อัปเดตข้อมูล Hardware Metrics เข้า State
    state.update_system_metrics(monitor.get_metrics())
    
    # 2. ดึงเฟรมภาพล่าสุดและ FPS/Resolution จาก Thread กล้องเข้าสู่ State Pool
    cam_manager.update_app_state_pool()
    
    # 3. เรนเดอร์คอมโพเนนต์ต่างๆ บน Dashboard
    render_top_status_bar()
    render_kpi_section()
    
    # สลับหน้าการแสดงผลตามปุ่มเมนูบน Sidebar
    if st.session_state.current_page == "Overview":
        render_system_status_and_logs()
    elif st.session_state.current_page == "Cameras":
        # เรียกหน้าจัดการกล้องที่เราจะเขียนใน Step ถัดไป
        from dashboard.camera_card import render_camera_management_page
        render_camera_management_page()

def render_dashboard():
    st.set_page_config(page_title="Real-Time Suspicious Behavior Detection", layout="wide")
    
    # ตรวจสอบการเปิดบริการกล้อง
    init_services()
    
    # ส่วนของ Sidebar ควบคุมการสลับหน้า (5 หน้าหลัก)
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Overview"
        
    st.sidebar.title("Navigation Menu")
    pages = ["Overview", "Cameras", "Live Streams", "Analytics", "Settings"]
    st.session_state.current_page = st.sidebar.radio("Go to", pages, index=pages.index(st.session_state.current_page))
    
    # กลไกสร้างเศษเสี้ยวหน้าจอสำหรับการรีเฟรชข้อมูลสดแบบ Real-time (Auto-refresh)
    @st.fragment(run_every=1.0)
    def auto_refresh_loop():
        refresh_container()
        
    auto_refresh_loop()