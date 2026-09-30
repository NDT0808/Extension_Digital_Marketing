from ultralytics import YOLO

def train_and_export():
    print("\n=== HUẤN LUYỆN YOLO-NANO (CLASSIFICATION) ===")
    
    # Tải mô hình YOLOv8-nano
    print("Đang tải YOLOv8-nano...")
    model = YOLO('yolov8n-cls.pt')
    
    # Bắt đầu huấn luyện (Train)
    print("🚀 Bắt đầu quá trình Training...")
    # imgsz=224 (ảnh kích thước lớn để AI nhìn rõ nét hơn, tránh đoán sai)
    # epochs=100 (tăng lên 100 để AI siêu chuẩn)
    # optimizer=AdamW, lr0=0.0001, batch=16 để hội tụ tốt hơn
    model.train(
        data='dog_dataset',
        epochs=150, 
        patience=50, # Dừng sớm nếu quá 50 epoch không cải thiện (chống overfitting)
        imgsz=224, 
        optimizer='AdamW', 
        lr0=0.0001, 
        batch=16,
        workers=0,
        # Các phép biến đổi ảnh (Augmentation) để mô phỏng video Reels thực tế
        degrees=10.0,    # Xoay ảnh nhẹ
        translate=0.1,   # Dịch chuyển ảnh
        scale=0.5,       # Phóng to / Thu nhỏ ngẫu nhiên
        fliplr=0.5,      # Lật ngang ảnh
        erasing=0.4      # Xóa ngẫu nhiên vài vùng để AI không học vẹt
    )
    
    # Xuất mô hình sang định dạng ONNX
    print("\n=== XUẤT MÔ HÌNH SANG APP PLUGIN (ONNX) ===")
    print("Đang chuyển đổi mô hình YOLO -> ONNX...")
    model.export(format='onnx')
    print("🎉 XONG! Mô hình ONNX của bạn đã sẵn sàng để nhúng vào Extension.")

if __name__ == '__main__':
    train_and_export()
