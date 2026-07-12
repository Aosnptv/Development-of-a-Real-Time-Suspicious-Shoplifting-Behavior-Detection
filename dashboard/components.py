import streamlit as st
from core.app_state import AppState
from services.config_service import ConfigService

# ประกาศตัวเรียกใช้งาน Service คอนฟิก
config_srv = ConfigService()

def get_status_badge(is_active, active_text="ONLINE", inactive_text="OFFLINE"):
    if is_active:
        return f'<span style="color:#2ecc71; font-weight:bold;">● {active_text}</span>'
    else:
        return f'<span style="color:#e74c3c; font-weight:bold;">● {inactive_text}</span>'

def render_top_status_bar():
    state = AppState()
    config = config_srv.load_config()
    metrics = state.system_metrics
    
    col_title, col_stat, col_mdl, col_ver, col_time = st.columns([2, 1, 1, 1, 1.5])
    
    with col_title:
        st.markdown("### Shoplifting Detection System")
    with col_stat:
        st.caption("System Status")
        st.markdown(get_status_badge(state.is_detector_running), unsafe_allow_html=True)
    with col_mdl:
        st.caption("Model Engine")
        st.write(config.get("model", "yolo11s.pt"))
    with col_ver:
        st.caption("Version")
        st.write("1.0.0")
    with col_time:
        st.caption("Current Time")
        st.write(metrics.get("time", "N/A"))
        
    st.write("---")

def render_bottom_subsystem_bar(cpu, ram, gpu):
    st.write("---")
    st.markdown("#### Subsystem Core Infrastructure Monitor")
    
    state = AppState()
    config = config_srv.load_config()
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    
    with c1:
        st.caption("CPU State")
        color = "#2ecc71" if cpu < 70 else ("#f1c40f" if cpu < 85 else "#e74c3c")
        st.markdown(f'<span style="color:{color}; font-weight:bold;">● {cpu}%</span>', unsafe_allow_html=True)
        
    with c2:
        st.caption("RAM State")
        color = "#2ecc71" if ram < 70 else ("#f1c40f" if ram < 85 else "#e74c3c")
        st.markdown(f'<span style="color:{color}; font-weight:bold;">● {ram}%</span>', unsafe_allow_html=True)
        
    with c3:
        st.caption("GPU State")
        color = "#2ecc71" if gpu < 75 else "#e74c3c"
        st.markdown(f'<span style="color:{color}; font-weight:bold;">● {gpu}%</span>', unsafe_allow_html=True)
        
    with c4:
        st.caption("SQLite DB")
        st.markdown(get_status_badge(state.is_db_connected, "CONNECTED", "DISCONNECTED"), unsafe_allow_html=True)
        
    with c5:
        st.caption("Telegram Bot")
        # ดึงสถานะเปิดใช้งานจากคอนฟิกหลัก
        tg_enabled = config.get("telegram", {}).get("enabled", False)
        st.markdown(get_status_badge(tg_enabled, "CONNECTED", "DISABLED"), unsafe_allow_html=True)
        
    with c6:
        st.caption("Camera Fleet")
        # คำนวณกล้องที่เปิดใช้งานอยู่จริงในระบบคอนฟิก
        cams = config.get("camera", {})
        active_cams = len(cams)
        st.markdown(f'<span style="color:#2ecc71; font-weight:bold;">● {active_cams} Registered</span>', unsafe_allow_html=True)
        
    with c7:
        st.caption("AI Detector")
        st.markdown(get_status_badge(state.is_detector_running, "PROCESSING", "IDLE"), unsafe_allow_html=True)