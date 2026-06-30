# app.py
import streamlit as st
import cv2
from ultralytics import YOLO
import numpy as np
import datetime
import time
# นำเข้าคลาสคำนวณโครงกระดูกและ FSM ที่เขียนแยกไว้
from behavior_analyzer import BehaviorAnalyzer 

# =====================================================================
# 1. คลาสสำหรับจัดการและจับคู่ชื่อ นาย A, B, C ข้ามกล้องด้วยคุณลักษณะสี (HSV)
# =====================================================================
class CrossCameraTracker:
    def __init__(self, target_names=["นาย A", "นาย B", "นาย C"], threshold=0.55):
        self.target_names = target_names
        self.threshold = threshold  # ค่าความเหมือนขั้นต่ำในการจับคู่ (0.0 ถึง 1.0)
        self.profiles = {}  # เก็บสถิติสีประจำตัว: {ชื่อ: hsv_histogram}
        self.camera_track_mappings = {}  # จับคู่ไอดีกล้องกับชื่อ: {(camera_id, local_track_id): ชื่อ}
        self.unassigned_names = list(target_names)

    def extract_features(self, frame, bbox):
        """[ปรับปรุง] สกัดคุณลักษณะสีเจาะจงเฉพาะ 'เสื้อท่อนบน' เพื่อลด Noise จากพื้นหลังและกางเกง"""
        x1, y1, x2, y2 = map(int, bbox)
        h, w, _ = frame.shape
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        
        # คำนวณความสูงของกรอบตรวจจับ
        box_height = y2 - y1
        
        # สไลซ์ภาพเฉพาะส่วนอกและลำตัว (ประมาณ 20% ถึง 60% ของความสูงกรอบ)
        y1_torso = y1 + int(box_height * 0.2)
        y2_torso = y1 + int(box_height * 0.6)
        
        crop = frame[y1_torso:y2_torso, x1:x2]
        if crop.size == 0:
            return None
        
        # แปลงเป็นพื้นที่สี HSV เพื่อเสถียรภาพต่อการเปลี่ยนแปลงของแสงข้ามมุมกล้อง
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        
        # คำนวณ Histogram ช่อง H และ S 
        hist = cv2.calcHist([hsv], [0, 1], None, [16, 16], [0, 180, 0, 256])
        cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
        return hist

    def get_person_name(self, camera_id, local_track_id, frame, bbox):
        """ค้นหาหรือระบุชื่อ นาย A, B, C ให้กับ ID ของกล้องนั้นๆ"""
        mapping_key = (camera_id, local_track_id)
        
        # 1. ถ้าไอดีของกล้องนี้เคยถูกระบุชื่อไปแล้ว ให้ส่งชื่อเดิมกลับไปทันที
        if mapping_key in self.camera_track_mappings:
            return self.camera_track_mappings[mapping_key]
        
        # 2. สกัดข้อมูลสีของคนที่เพิ่งเจอใหม่
        current_hist = self.extract_features(frame, bbox)
        if current_hist is None:
            return "ไม่ระบุตัวตน"
            
        best_match_name = None
        best_score = -1
        
        # 3. เปรียบเทียบกับกลุ่มคนที่เคยลงทะเบียนไว้แล้ว (นาย A, B, C)
        for name, profile_hist in self.profiles.items():
            score = cv2.compareHist(profile_hist, current_hist, cv2.HISTCMP_CORREL)
            if score > best_score:
                best_score = score
                best_match_name = name
                
        # 4. ถ้ามีความคล้ายคลึงกันมากกว่าค่า Threshold แสดงว่าเป็นคนเดียวกันจากอีกกล้อง
        if best_score > self.threshold and best_match_name is not None:
            self.camera_track_mappings[mapping_key] = best_match_name
            # อัปเดตคุณลักษณะสีแบบถ่วงน้ำหนัก (Exponential Moving Average) เพื่อจำสีตามสภาพแสงกล้องใหม่
            self.profiles[best_match_name] = 0.7 * self.profiles[best_match_name] + 0.3 * current_hist
            return best_match_name
            
        # 5. ถ้าไม่เหมือนใครเลย และยังมีชื่อเหลืออยู่ในระบบ ให้ลงทะเบียนชื่อใหม่ให้กับคนนี้
        if self.unassigned_names:
            new_name = self.unassigned_names.pop(0)
            self.profiles[new_name] = current_hist
            self.camera_track_mappings[mapping_key] = new_name
            return new_name
            
        return "บุคคลอื่น"

    def reset(self):
        """ล้างค่าระบบติดตามใหม่ทั้งหมด"""
        self.profiles.clear()
        self.camera_track_mappings.clear()
        self.unassigned_names = list(self.target_names)


# =====================================================================
# 2. ส่วนหน้าจอแสดงผลหลัก Web Application ด้วย Streamlit
# =====================================================================
st.set_page_config(page_title="CCTV Control Center", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <h2 style='text-align: left; font-weight: 600; font-family: sans-serif; margin-bottom: 5px;'>
        CCTV Monitor & Behavior Analysis System (FSM + Cross-Camera Tracking)
    </h2>
    <div style='border-bottom: 2px solid #E2E8F0; margin-bottom: 20px;'></div>
""", unsafe_allow_html=True)

@st.cache_resource
def load_models():
    pose_model = YOLO('yolov8n-pose.pt') 
    object_model = YOLO('yolov8n.pt')   
    return pose_model, object_model

pose_model, object_model = load_models()

@st.cache_resource
def init_analyzer():
    return BehaviorAnalyzer()

analyzer = init_analyzer()

if 'cross_tracker' not in st.session_state:
    st.session_state.cross_tracker = CrossCameraTracker()

tracker = st.session_state.cross_tracker

CAM_SOURCES = {
    "CAM 01": {"source": 0, "name": "โซนเคาน์เตอร์ชำระเงิน"},
    "CAM 02": {"source": 1, "name": "โซนชั้นวางสินค้า A"},
    "CAM 03": {"source": 2, "name": "โซนชั้นวางสินค้า B"},
    "CAM 04": {"source": 3, "name": "โซนประตูทางเข้า-ออก"}
}

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "Grid 2x2"

if "system_logs" not in st.session_state:
    st.session_state.system_logs = ["[00:00:00] SYSTEM - เปิดใช้งานกลไกคำนวณพฤติกรรม FSM ล็อกพิกัดสัดส่วน"]

st.sidebar.markdown("### แผงควบคุมระบบ")
run_system = st.sidebar.toggle("เปิดการทำงานของระบบ", value=False)

st.sidebar.markdown("---")
st.sidebar.markdown("#### 👤 ตั้งค่าการตรวจจับคนข้ามกล้อง")
hist_threshold = st.sidebar.slider("ระดับความเข้มงวดในการเทียบสี (Threshold)", 0.3, 0.9, 0.55, 0.05)
tracker.threshold = hist_threshold

if st.sidebar.button("♻️ รีเซ็ตระบบจดจำชื่อบุคคล", use_container_width=True):
    tracker.reset()
    st.sidebar.success("รีเซ็ตระบบลงทะเบียนรายชื่อเรียบร้อยแล้ว!")

st.sidebar.markdown("---")
st.sidebar.markdown("#### มุมมองกล้อง")

is_grid_active = (st.session_state.view_mode == "Grid 2x2")
if st.sidebar.button("Grid 2x2", type="primary" if is_grid_active else "secondary", use_container_width=True):
    st.session_state.view_mode = "Grid 2x2"; st.rerun()

c_col1, c_col2 = st.sidebar.columns(2)
with c_col1:
    if st.button("CAM 01", type="primary" if st.session_state.view_mode == "CAM 01" else "secondary", use_container_width=True):
        st.session_state.view_mode = "CAM 01"; st.rerun()
    if st.button("CAM 03", type="primary" if st.session_state.view_mode == "CAM 03" else "secondary", use_container_width=True):
        st.session_state.view_mode = "CAM 03"; st.rerun()
with c_col2:
    if st.button("CAM 02", type="primary" if st.session_state.view_mode == "CAM 02" else "secondary", use_container_width=True):
        st.session_state.view_mode = "CAM 02"; st.rerun()
    if st.button("CAM 04", type="primary" if st.session_state.view_mode == "CAM 04" else "secondary", use_container_width=True):
        st.session_state.view_mode = "CAM 04"; st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("#### บันทึกเหตุการณ์ระบบ (System Logs)")
log_display_text = "\n".join(st.session_state.system_logs[-6:])
st.sidebar.code(log_display_text, language="bash")

# จองบล็อก UI แสดงผลกล้อง
view_mode = st.session_state.view_mode
frame_places = {}
score_places = {}

if view_mode == "Grid 2x2":
    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)
    cols = [row1_col1, row1_col2, row2_col1, row2_col2]
    for idx, cam_id in enumerate(CAM_SOURCES.keys()):
        with cols[idx]:
            st.markdown(f"**{cam_id}: {CAM_SOURCES[cam_id]['name']}**")
            frame_places[cam_id] = st.empty()
            score_places[cam_id] = st.empty()
else:
    st.markdown(f"### มุมมองขยาย: {view_mode} ({CAM_SOURCES[view_mode]['name']})")
    frame_places[view_mode] = st.empty()
    score_places[view_mode] = st.empty()

# --- สถานะระบบสแตนด์บาย ---
if not run_system:
    for cam_id in frame_places.keys():
        standby_frame = np.ones((270, 480, 3), dtype=np.uint8) * 235
        cv2.putText(standby_frame, "SYSTEM STANDBY", (140, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (160, 174, 192), 2)
        standby_rgb = cv2.cvtColor(standby_frame, cv2.COLOR_BGR2RGB)
        frame_places[cam_id].image(standby_rgb, channels="RGB", use_container_width=True)
        score_places[cam_id].caption("สถานะ: ปิดการทำงาน (กรุณากดสวิตช์แผงควบคุมด้านซ้าย)")

# --- ลูปดึงภาพกล้องจริงทำงานสดเรียลไทม์ ---
else:
    caps = {}
    for cam_id, config in CAM_SOURCES.items():
        caps[cam_id] = cv2.VideoCapture(config["source"])

    FRAME_SKIP = 3
    frame_counter = 0
    cached_outputs = {cam_id: None for cam_id in CAM_SOURCES.keys()}

    while True:
        frame_counter += 1
        
        for cam_id, cap in caps.items():
            if view_mode != "Grid 2x2" and cam_id != view_mode:
                continue

            success, frame = cap.read()
            if not success:
                frame_out = np.ones((270, 480, 3), dtype=np.uint8) * 230
                cv2.putText(frame_out, f"{cam_id} OFFLINE", (140, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (148, 163, 184), 2)
                risk_text = "สถานะ: ไม่สามารถเชื่อมต่อสายสัญญาณกล้องได้"
                frame_rgb = cv2.cvtColor(frame_out, cv2.COLOR_BGR2RGB)
                if cam_id in frame_places:
                    frame_places[cam_id].image(frame_rgb, channels="RGB", use_container_width=True)
                    score_places[cam_id].caption(risk_text)
                continue

            if frame_counter % FRAME_SKIP == 0 or cached_outputs[cam_id] is None:
                pose_res = pose_model.track(frame, persist=True, verbose=False)
                obj_res = object_model(frame, verbose=False)
                
                # [แก้ไข] เรียกส่งวิเคราะห์ผลผ่านระบบ FSM คะแนนรวมประจำกล้องขึ้นมาก่อน เพื่อเตรียมนำไปวาดบนตัวคน
                current_score, current_state, log_message = analyzer.analyze_pose_and_objects(cam_id, pose_res, obj_res)
                
                state_titles = ["Idle (ปกติ)", "Picking", "Holding", "Concealing"]
                current_title = state_titles[current_state]
                
                # วาดเส้นจุดโครงกระดูก (ปิดการแสดงฉลาก 'person' ดั้งเดิมของ YOLO)
                frame_out = pose_res[0].plot(labels=False)
                if len(obj_res) > 0 and obj_res[0].boxes is not None:
                    frame_out = obj_res[0].plot(img=frame_out)
                
                # [แก้ไขลำดับ] จับคู่ชื่อข้ามกล้อง และประกอบข้อความคะแนนความเสี่ยงเพื่อสลักลงตัวบุคคล
                if pose_res and pose_res[0].boxes is not None and pose_res[0].boxes.id is not None:
                    boxes = pose_res[0].boxes.xyxy.cpu().numpy()
                    ids = pose_res[0].boxes.id.cpu().numpy().astype(int)
                    
                    for bbox, t_id in zip(boxes, ids):
                        # จับคู่สถิติสีเพื่อระบุชื่อ นาย A, B, C ดั้งเดิม
                        display_name = tracker.get_person_name(camera_id=cam_id, local_track_id=t_id, frame=frame, bbox=bbox)
                        
                        # [เพิ่มประสิทธิภาพ] ผสานชื่อพ่วงด้วยสถานะ FSM และคะแนนความเสี่ยง (เช่น "นาย A | Holding (Score: 3/5)")
                        person_label = f"{display_name} | {current_title} ({current_score}/5)"
                        
                        x1, y1, x2, y2 = map(int, bbox)
                        
                        # ปรับแต่งสีกรอบตามระดับความเสี่ยงของกล้อง
                        box_color = (0, 0, 255) if current_score >= 4 else ((0, 165, 255) if current_score >= 2 else (0, 255, 0))
                        
                        # วาดกรอบสี่เหลี่ยมรอบตัวบุคคลและเขียนชื่อพร้อมคะแนนทับลงไปขนานกัน
                        cv2.rectangle(frame_out, (x1, y1), (x2, y2), box_color, 2)
                        cv2.putText(frame_out, person_label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 2)

                frame_out = cv2.resize(frame_out, (480, 270))
                
                if current_score >= 5:
                    risk_text = f"🚨 ดัชนีความเสี่ยงพฤติกรรม: {current_score} / 5 [{current_title}] - ตรวจพบเหตุต้องสงสัย!"
                elif current_score >= 2:
                    risk_text = f"⚠️ ดัชนีความเสี่ยงพฤติกรรม: {current_score} / 5 [{current_title}] - กำลังตรวจสอบต่อเนื่อง"
                else:
                    risk_text = f"ดัชนีความเสี่ยงพฤติกรรม: {current_score} / 5 [{current_title}] - ปกติ"

                if log_message:
                    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                    st.session_state.system_logs.append(f"[{timestamp}] {log_message}")
                
                cached_outputs[cam_id] = (frame_out, risk_text)
            else:
                frame_out, risk_text = cached_outputs[cam_id]

            frame_rgb = cv2.cvtColor(frame_out, cv2.COLOR_BGR2RGB)
            if cam_id in frame_places:
                frame_places[cam_id].image(frame_rgb, channels="RGB", use_container_width=True)
                score_places[cam_id].caption(risk_text)

        time.sleep(0.01)
        if not run_system:
            break

    for cap in caps.values():
        cap.release()