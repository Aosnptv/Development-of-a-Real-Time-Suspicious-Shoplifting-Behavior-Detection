from ultralytics import YOLO

def main():
    print("🚀 กำลังเริ่มต้นการฝึกสอน (Train) YOLO11s...")

    model = YOLO("yolo11s.pt") 

    results = model.train(
        data="dataset/dataset.yaml",
        epochs=100,                  
        imgsz=640,                   
        batch=16,                    
        patience=20,                 
        name="shoplifting_model_v1", 
        device="cpu"                # 🟢 เปลี่ยนจาก "auto" เป็น "cpu" ตรงนี้ครับ
    )

    print("🎉 การฝึกสอนเสร็จสิ้น!")

if __name__ == "__main__":
    main()