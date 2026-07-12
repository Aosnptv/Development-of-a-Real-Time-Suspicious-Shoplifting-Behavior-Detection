import streamlit as st
from core.app_state import AppState

def render_kpi_section():
    state = AppState()
    
    # ดึงค่าล่าสุดจากระบบฝาก Cache ส่วนกลาง (AppState)
    metrics = state.system_metrics
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric(label="Alerts Today", value=str(state.alerts_today))
    with col2:
        st.metric(label="CPU Usage", value=f"{metrics.get('cpu', 0.0)} %")
    with col3:
        st.metric(label="RAM Usage", value=f"{metrics.get('ram', 0.0)} %")
    with col4:
        st.metric(label="Cameras Online", value="2 / 4")  # จะเชื่อมโยงอัตโนมัติใน Sprint หน้า
    with col5:
        st.metric(label="FPS Average", value=f"{state.fps_average} fps")
    with col6:
        st.metric(label="System Uptime", value=metrics.get('uptime', '00h 00m 00s'))
        
    st.write("---")