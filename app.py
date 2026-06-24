import streamlit as st
import cv2
from ultralytics import YOLO
import numpy as np

# ตั้งค่าหน้าจอแบบกว้าง (Wide)
st.set_page_config(
    page_title="CCTV Control Center", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# ส่วนหัวระบบ: ถอดการล็อกรหัสสีออก เพื่อให้รองรับโหมดมืด (ข้อความจะเปลี่ยนเป็นสีขาวอัตโนมัติ)
st.markdown("""
    <h2 style='text-align: left; font-weight: 600; font-family: sans-serif; margin-bottom: 5px;'>
        CCTV Monitor & Behavior Analysis System
    </h2>
    <div style='border-bottom: 2px solid #E2E8F0; margin-bottom: 20px;'></div>
""", unsafe_allow_html=True)

# โหลดโมเดลสำหรับประมวลผล AI
@st.cache_resource
def load_model():
    return YOLO('yolov8n.pt')

model = load_model()

# กำหนดค่ากล้องทั้งหมดในระบบ
CAM_SOURCES = {
    "CAM 01": {"source": 0, "name": "โซนเคาน์เตอร์ชำระเงิน"},
    "CAM 02": {"source": 1, "name": "โซนชั้นวางสินค้า A"},
    "CAM 03": {"source": 2, "name": "โซนชั้นวางสินค้า B"},
    "CAM 04": {"source": 3, "name": "โซนประตูทางเข้า-ออก"}
}

# --- การจัดการสถานะปุ่มกดสลับมุมมอง (Toggle States) ---
# กำหนดค่าเริ่มต้นให้กับมุมมองกล้อง หากยังไม่มีในระบบความจำ (Session State)
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "แสดงกล้องทั้งหมด (Grid 2x2)"

# --- แถบควบคุมด้านซ้าย (Sidebar) ---
st.sidebar.markdown("### แผงควบคุมระบบ")

# ใช้สวิตช์เปิด/ปิดแบบเรียบหรูสไตล์มินิมอลแทน Checkbox เดิม
run_system = st.sidebar.toggle("เปิดการทำงานของระบบ", value=False)

st.sidebar.markdown("---")
st.sidebar.markdown("#### เลือกมุมมองกล้อง")

# รายการเมนูทั้งหมดที่ผู้ใช้สามารถกดเลือกได้
view_options = ["แสดงกล้องทั้งหมด (Grid 2x2)"] + list(CAM_SOURCES.keys())

# วนลูปสร้างปุ่มกดแบบ Toggle State แทนเมนู Radio
for option in view_options:
    # ตรวจสอบว่าปุ่มนี้คือปุ่มที่กำลังใช้งานอยู่หรือไม่
    is_active = (st.session_state.view_mode == option)
    
    # ถ้าเป็นปุ่มที่กำลังเปิดอยู่ ให้ใช้สีเด่น (primary) ถ้าไม่ใช่ให้ใช้สีพื้นฐาน (secondary)
    if st.sidebar.button(
        option, 
        type="primary" if is_active else "secondary", 
        use_container_width=True
    ):
        st.session_state.view_mode = option
        st.rerun() # สั่งรีเฟรชหน้าเว็บทันทีเพื่อให้เปลี่ยนโหมดมุมกล้องนิ่งและเสถียรขึ้น

st.sidebar.markdown("---")
st.sidebar.markdown("#### บันทึกเหตุการณ์ระบบ")

# บันทึกสถานะใช้ตารางโค้ดดั้งเดิม เพื่อให้ตัวหนังสือเปลี่ยนสีตามโหมดมืด/สว่างได้สมบูรณ์แบบ
log_text = (
    "[14:22:10] SYSTEM - เริ่มต้นการเชื่อมต่อกล้อง\n"
    "[14:22:12] CAM 01 - ตรวจพบพฤติกรรมเสี่ยง [ALERT]\n"
    "[14:22:15] CAM 02 - ตรวจพบการหยิบสินค้าปกติ"
)
st.sidebar.code(log_text, language="bash")


# --- พื้นที่แสดงผลมอนิเตอร์หลัก (Main Area) ---
view_mode = st.session_state.view_mode

if run_system:
    # เริ่มต้นเชื่อมต่อกล้องทุกตัว
    caps = {}
    for cam_id, config in CAM_SOURCES.items():
        caps[cam_id] = cv2.VideoCapture(config["source"])

    # สร้างบล็อกจองพื้นที่แสดงผลภาพวิดีโอ
    frame_places = {}
    score_places = {}

    if view_mode == "แสดงกล้องทั้งหมด (Grid 2x2)":
        # จัด Layout หน้าจอเป็น 2 แถว แถวละ 2 คอลัมน์
        row1_col1, row1_col2 = st.columns(2)
        row2_col1, row2_col2 = st.columns(2)
        
        cols = [row1_col1, row1_col2, row2_col1, row2_col2]
        for idx, cam_id in enumerate(CAM_SOURCES.keys()):
            with cols[idx]:
                st.markdown(f"**{cam_id}: {CAM_SOURCES[cam_id]['name']}**")
                frame_places[cam_id] = st.empty()
                score_places[cam_id] = st.empty()
    else:
        # มุมมองขยายแบบกล้องตัวเดียวเต็ม ๆ จอ
        st.markdown(f"### มุมมองขยาย: {view_mode} ({CAM_SOURCES[view_mode]['name']})")
        frame_places[view_mode] = st.empty()
        score_places[view_mode] = st.empty()


    # ลูปหลักในการดึงเฟรมภาพมาแสดงผลแบบเรียลไทม์
    while True:
        for cam_id, cap in caps.items():
            # ข้ามการประมวลผลกล้องตัวอื่น หากอยู่ในโหมดขยายกล้องเดี่ยวเพื่อประหยัด CPU
            if view_mode != "แสดงกล้องทั้งหมด (Grid 2x2)" and cam_id != view_mode:
                continue

            success, frame = cap.read()

            if not success:
                # สร้างหน้าจอออฟไลน์สีเทา (ปรับขนาดให้เล็กลงเพื่อบีบหน้าจอไม่ให้เกิดการ Scroll)
                frame_out = np.ones((270, 480, 3), dtype=np.uint8) * 230
                cv2.putText(frame_out, f"{cam_id} OFFLINE", (140, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (148, 163, 184), 2)
                risk_text = "สถานะ: ไม่สามารถเชื่อมต่อได้"
            else:
                # หากดึงภาพสำเร็จ ส่งเข้าโมเดล AI
                results = model(frame)
                frame_out = results[0].plot()
                
                # **จุดสำคัญ:** ทำการบีบย่อขนาดภาพ (Resize) เป็น 480x270 พิกเซล 
                # เพื่อให้ภาพทั้ง 4 ช่องกระชับ รวมกันแล้วแสดงผลครบภายใน 1 หน้าจอพอดีโดยไม่ต้องเลื่อนลง
                frame_out = cv2.resize(frame_out, (480, 270))
                risk_text = "ดัชนีความเสี่ยงพฤติกรรม: 0 / 5 (ปกติ)"

            # แปลงระบบสีภาพให้ถูกต้องสำหรับขึ้นหน้าเว็บ
            frame_rgb = cv2.cvtColor(frame_out, cv2.COLOR_BGR2RGB)

            # อัปเดตภาพขึ้นบนหน้าจอ UI
            if cam_id in frame_places:
                frame_places[cam_id].image(frame_rgb, channels="RGB", use_container_width=True)
                score_places[cam_id].caption(risk_text) # ใช้ st.caption เพื่อให้ตัวหนังสือปรับสีตามโหมดมืดอัตโนมัติ

        # ดักจับกรณีผู้ใช้ปิดสวิตช์ระบบที่แถบข้างเพื่อหยุดลูปการทำงาน
        if not run_system:
            break

    # ปิดตัวจับภาพและคืนทรัพยากรให้คอมพิวเตอร์
    for cap in caps.values():
        cap.release()

else:
    # ข้อความต้อนรับเริ่มต้น (ปรับสีข้อความอัตโนมัติตามโหมดมืด/สว่าง)
    st.markdown("ระบบพร้อมใช้งาน กรุณากดเปิดสวิตช์ที่แผงควบคุมด้านซ้ายเพื่อเริ่มต้นมอนิเตอร์กล้องวงจรปิด")