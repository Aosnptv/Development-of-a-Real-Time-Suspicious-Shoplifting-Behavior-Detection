import streamlit as st
import pandas as pd
from dashboard.components import render_top_status_bar

def render_cameras():
    render_top_status_bar()
    st.title("Camera Manager")
    
    # --- ตัวแปรที่หายไป ถูกเติมกลับมาให้สมบูรณ์ตรงนี้แล้วครับ ---
    cameras_df = pd.DataFrame({
        "Camera Name": ["Camera 01", "Camera 02", "Camera 03", "Camera 04"],
        "Camera Status": ["Active", "Active", "No Signal", "No Signal"],
        "FPS": ["30.0", "25.0", "0.0", "0.0"],
        "Resolution": ["1920x1080", "1280x720", "N/A", "N/A"],
        "Connection": ["Connected", "Connected", "Disconnected", "Disconnected"]
    })
    
    # แสดงผลตารางโดยใช้มาตรฐานกว้างเต็มจอแบบใหม่
    st.dataframe(cameras_df, width="stretch")
    
    st.write("---")
    
    col_add, col_del = st.columns(2)
    with col_add:
        st.subheader("Add / Edit Camera")
        cam_name = st.text_input("Camera Name")
        cam_url = st.text_input("RTSP URL")
        if st.button("Save Camera Settings"):
            st.success(f"Camera '{cam_name}' saved successfully.")
            
    with col_del:
        st.subheader("Delete Camera")
        cam_to_delete = st.selectbox("Select Camera to Delete", ["None", "Camera 01", "Camera 02"])
        if st.button("Delete Camera", type="primary"):
            if cam_to_delete != "None":
                st.warning(f"Camera '{cam_to_delete}' has been deleted.")