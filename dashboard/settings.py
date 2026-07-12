import streamlit as st
from dashboard.components import render_top_status_bar

def render_settings():
    render_top_status_bar()
    st.title("Settings")
    
    st.subheader("Model & Detection Settings")
    st.selectbox("Model Selection", ["YOLOv11s", "custom.pt"])
    st.slider("Confidence Threshold", 0.0, 1.0, 0.25, step=0.05)
    
    col_save, col_load, col_reset = st.columns(3)
    with col_save:
        st.button("Save Settings", use_container_width=True)
    with col_load:
        st.button("Load Settings", use_container_width=True)
    with col_reset:
        st.button("Reset to Default", type="primary", use_container_width=True)