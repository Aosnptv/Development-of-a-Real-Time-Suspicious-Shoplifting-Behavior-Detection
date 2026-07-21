from ultralytics import YOLO

# ใส่ Path ไฟล์ weight ของคุณ
model = YOLO("C:/Users/deeny/Downloads/Data/Store-Behavior-YOLO11.v2i.yolov11/data.yaml")

print("ลำดับ Class ที่โมเดลจำอยู่ตอนนี้:")
print(model.names)