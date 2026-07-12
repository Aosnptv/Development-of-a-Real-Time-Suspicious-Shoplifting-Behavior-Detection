import streamlit as st
import database.database as db
from dashboard.components import render_top_status_bar

def render_history():
    render_top_status_bar()
    st.title("Incident History")
    
    # เปลี่ยนมาดึงข้อมูลจริงจากคำสั่ง SQL Query ผ่านตัวครอบระบบฐานข้อมูล
    df = db.get_all_incidents()
    
# ส่วนหนึ่งของโค้ดในไฟล์ history.py
    if not df.empty:
        status_filter = st.selectbox("Filter by Status", ["All", "Unresolved", "Resolved"])
        if status_filter != "All":
            df = df[df["Status"] == status_filter]
            
        # แก้อาร์กิวเมนต์ตรงนี้ จาก use_container_width=True
        st.dataframe(df, width="stretch")
        
        st.write("---")
        st.subheader("View Selected Incident Image")
        selected_row = st.selectbox(
            "Select Row to View Image", 
            df.index, 
            format_func=lambda x: f"Row {x} - {df.loc[x, 'time']} - {df.loc[x, 'camera']}"
        )
        
        image_url = df.loc[selected_row, "image"]
        st.image(image_url, caption=f"Snapshot for Person: {df.loc[selected_row, 'person']}", width=300)
    else:
        st.info("No incidents recorded in the database.")
