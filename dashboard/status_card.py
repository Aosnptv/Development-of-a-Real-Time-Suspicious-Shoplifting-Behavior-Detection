import streamlit as st
from core.app_state import AppState
from services.logger import logger

def render_system_status_and_logs():
    state = AppState()
    
    # ดึงข้อมูลฮาร์ดแวร์ล่าสุดจาก AppState
    metrics = state.system_metrics

    st.markdown("### System Diagnostics & Activity Logs")
    
    col_status, col_logs = st.columns([1, 2])
    
    with col_status:
        st.markdown("#### Hardware Health")
        
        # เปลี่ยนมาดึงค่าจาก dictionary ที่เก็บข้อมูลสดจาก SystemMonitor
        st.text_input("CPU Usage", value=f"{metrics.get('cpu', 0.0)} %", disabled=True)
        st.text_input("RAM Usage", value=f"{metrics.get('ram', 0.0)} %", disabled=True)
        st.text_input("GPU Usage", value=f"{metrics.get('gpu', 0.0)} %", disabled=True)
        st.text_input("Disk Storage", value=f"{metrics.get('disk', 0.0)} %", disabled=True)
        st.text_input("Network Data Flow", value=metrics.get('network', '↑ 0.0MB / ↓ 0.0MB'), disabled=True)

    with col_logs:
        st.markdown("#### Real-time Activity Logs")
        
        # ดึงประวัติ Log จากระบบ Logger กลางมาแสดงผล
        recent_logs = logger.get_recent_logs(limit=10)
        
        if recent_logs:
            st.dataframe(
                recent_logs, 
                use_container_width=True,
                column_config={
                    "Time": st.column_config.TextColumn("Timestamp", width="small"),
                    "Level": st.column_config.TextColumn("Level", width="small"),
                    "Event": st.column_config.TextColumn("System Event Description", width="large")
                }
            )
        else:
            st.info("No system events recorded yet.")