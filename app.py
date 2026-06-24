import streamlit as st
import cv2
from ultralytics import YOLO
import numpy as np

# ตั้งค่าหน้าเว็บแบบกว้างและใช้โครงสร้างที่สะอาดตา
st.set_page_config(
    page_title="CCTV Control Center", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# ส่วนหัวของระบบ (ใช้ฟอนต์แนว Sans-serif และสีโทนเข้มสุภาพ)
st.markdown("""
    <h2 style='text-align: left; color: #1E293B; font-weight: 600; font-family: sans-serif; margin-bottom: 5px;'>
        ระบบควบคุมกล้องวงจรปิด (CCTV Control Center)
    </h2>
    <div style='border-bottom: 2px solid #E2E8F0; margin-bottom: 25px;'></div>
""", unsafe_allow_html=True)

# โหลดโมเดลสำหรับประมวลผล
@st.cache_resource
def load_model():
    return YOLO('yolov8n.pt')

model = load_model()

# --- แถบควบคุมด้านซ้าย (Sidebar) ---
st.sidebar.markdown("<h3 style='color: #1E293B; font-weight: 500; font-size: 18px;'>แผงควบคุมระบบ</h3>", unsafe_allow_html=True)

# 1. ปุ่มสวิตช์เปิด/ปิดระบบแบบเรียบๆ
run_system = st.sidebar.checkbox("เปิดการทำงานของระบบ", value=False)

# 2. เมนูเลือกมุมมองกล้อง
view_mode = st.sidebar.radio(
    "เลือกมุมมองกล้อง",
    ["แสดงกล้องทั้งหมด (Grid 2x1)", "กล้อง 1: โซนเคาน์เตอร์", "กล้อง 2: โซนชั้นวางสินค้า"]
)

st.sidebar.markdown("<div style='border-bottom: 1px solid #E2E8F0; margin: 25px 0;'></div>", unsafe_allow_html=True)
st.sidebar.markdown("<h4 style='color: #1E293B; font-weight: 500; font-size: 15px;'>บันทึกเหตุการณ์ล่าสุด</h4>", unsafe_allow_html=True)

# ส่วนแสดง Log เหตุการณ์ในสไตล์ Terminal/Monospace สีดาร์กเกรย์ เรียบง่ายและเป็นทางการ
st.sidebar.markdown("""
    <div style='font-family: monospace; font-size: 12px; color: #475569; background-color: #F8FAFC; padding: 10px; border-radius: 4px; border: 1px solid #E2E8F0;'>
        [12:31:05] CAM 01 - พฤติกรรมต้องสงสัย <span style='color: #DC2626; font-weight: bold;'>[ALERT]</span><br>
        [12:15:20] CAM 02 - ตรวจพบการหยิบสินค้าปกติ<br>
        [12:02:44] CAM 01 - ตรวจพบการหยิบสินค้าปกติ
    </div>
""", unsafe_allow_html=True)


# --- พื้นที่มอนิเตอร์หลัก (Main Monitor Area) ---
if run_system:
    # เริ่มดึงข้อมูลจาก Source กล้อง (สามารถเปลี่ยนเลขเป็นพาร์ทวิดีโอได้)
    cap1 = cv2.VideoCapture(0)  
    cap2 = cv2.VideoCapture(1)  

    # จัดหน้าตา Layout ตามโหมดที่ผู้ใช้เลือก
    if view_mode == "แสดงกล้องทั้งหมด (Grid 2x1)":
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<p style='font-weight: 500; color: #475569; margin-bottom: 5px; font-size: 14px;'>CAM 01: โซนเคาน์เตอร์</p>", unsafe_allow_html=True)
            frame_place1 = st.empty()
            score_place1 = st.empty()
        with col2:
            st.markdown("<p style='font-weight: 500; color: #475569; margin-bottom: 5px; font-size: 14px;'>CAM 02: โซนชั้นวางสินค้า</p>", unsafe_allow_html=True)
            frame_place2 = st.empty()
            score_place2 = st.empty()

    elif view_mode == "กล้อง 1: โซนเคาน์เตอร์":
        st.markdown("<p style='font-weight: 500; color: #475569; margin-bottom: 5px; font-size: 14px;'>มุมมองขยาย: CAM 01 (โซนเคาน์เตอร์)</p>", unsafe_allow_html=True)
        frame_place_single = st.empty()
        score_place_single = st.empty()

    elif view_mode == "กล้อง 2: โซนชั้นวางสินค้า":
        st.markdown("<p style='font-weight: 500; color: #475569; margin-bottom: 5px; font-size: 14px;'>มุมมองขยาย: CAM 02 (โซนชั้นวางสินค้า)</p>", unsafe_allow_html=True)
        frame_place_single = st.empty()
        score_place_single = st.empty()


    # ลูปหลักในการดึงเฟรมภาพมาแสดงผล
    while cap1.isOpened() or cap2.isOpened():
        success1, frame1 = cap1.read()
        success2, frame2 = cap2.read()

        # กรณีกล้องไม่ทำงาน ให้ขึ้นหน้าจอออฟไลน์สีเทาแทนสีดำฉูดฉาด
        if not success1:
            frame1 = np.ones((480, 640, 3), dtype=np.uint8) * 240 # หน้าจอสีเทาอ่อน
            cv2.putText(frame1, "CAMERA 01 OFFLINE", (160, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (148, 163, 184), 2)
        if not success2:
            frame2 = np.ones((480, 640, 3), dtype=np.uint8) * 240
            cv2.putText(frame2, "CAMERA 02 OFFLINE", (160, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (148, 163, 184), 2)

        # ส่งภาพไปประมวลผลผ่านโมเดล AI
        if success1:
            res1 = model(frame1)
            frame1_out = res1[0].plot()
        else:
            frame1_out = frame1

        if success2:
            res2 = model(frame2)
            frame2_out = res2[0].plot()
        else:
            frame2_out = frame2

        # แปลงสีให้เข้ากับระบบเว็บสตรีมมิ่ง
        frame1_rgb = cv2.cvtColor(frame1_out, cv2.COLOR_BGR2RGB)
        frame2_rgb = cv2.cvtColor(frame2_out, cv2.COLOR_BGR2RGB)

        # อัปเดตการแสดงผลบน UI ตามโหมดมุมมองที่เลือกไว้
        if view_mode == "แสดงกล้องทั้งหมด (Grid 2x1)":
            frame_place1.image(frame1_rgb, channels="RGB", use_column_width=True)
            score_place1.markdown("<p style='font-size: 13px; color: #64748B;'>ดัชนีความเสี่ยงพฤติกรรม: 2 / 5 (ปกติ)</p>", unsafe_allow_html=True)
            
            frame_place2.image(frame2_rgb, channels="RGB", use_column_width=True)
            score_place2.markdown("<p style='font-size: 13px; color: #64748B;'>ดัชนีความเสี่ยงพฤติกรรม: 0 / 5 (ปกติ)</p>", unsafe_allow_html=True)

        elif view_mode == "กล้อง 1: โซนเคาน์เตอร์":
            frame_place_single.image(frame1_rgb, channels="RGB", use_column_width=True)
            score_place_single.markdown("<p style='font-size: 14px; color: #64748B; font-weight: 500;'>ดัชนีความเสี่ยงพฤติกรรม: 2 / 5 (ปกติ)</p>", unsafe_allow_html=True)

        elif view_mode == "กล้อง 2: โซนชั้นวางสินค้า":
            frame_place_single.image(frame2_rgb, channels="RGB", use_column_width=True)
            score_place_single.markdown("<p style='font-size: 14px; color: #64748B; font-weight: 500;'>ดัชนีความเสี่ยงพฤติกรรม: 0 / 5 (ปกติ)</p>", unsafe_allow_html=True)

    cap1.release()
    cap2.release()

else:
    # ข้อความเริ่มต้นเมื่อเปิดระบบขึ้นมาครั้งแรก (ดีไซน์เรียบๆ)
    st.markdown("<p style='color: #94A3B8; font-size: 14px; text-align: left;'>กรุณาเปิดการทำงานของระบบเพื่อเริ่มต้นการตรวจสอบกล้องวงจรปิด</p>", unsafe_allow_html=True)