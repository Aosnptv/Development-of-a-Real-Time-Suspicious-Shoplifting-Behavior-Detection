import streamlit as st
from dashboard.dashboard import render_dashboard
from dashboard.history import render_history
from dashboard.analytics import render_analytics
from dashboard.cameras import render_cameras
from dashboard.settings import render_settings

# ตั้งค่า Configuration หลัก
st.set_page_config(
    page_title="Shoplifting Detection System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------
# NAVIGATION ROUTER
# ----------------------------------------------------
st.sidebar.title("System Menu")
page = st.sidebar.radio(
    "Select View",
    ["Dashboard", "Incident History", "Analytics", "Camera Manager", "Settings"]
)

st.sidebar.write("---")
st.sidebar.caption("System Version: 3.0.0 (Sprint 3)")

# สั่งเรนเดอร์ตามหน้าที่เลือก (จบหน้าที่ในไฟล์หลัก)
if page == "Dashboard":
    render_dashboard()
elif page == "Incident History":
    render_history()
elif page == "Analytics":
    render_analytics()
elif page == "Camera Manager":
    render_cameras()
elif page == "Settings":
    render_settings()